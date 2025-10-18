
"""
optimizer.py — v4.3.0
Classic 9-man lineup logic (QB, 2 RB, 3 WR, TE, FLEX, DST).
FLEX can be RB/WR/TE regardless of main slot counts.
Maintained by: KyRockHunter
"""

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import pulp


@dataclass
class OptimizeResult:
    lineup: pd.DataFrame
    salary: float
    ev: float
    objective: float

    def is_valid(self) -> bool:
        return isinstance(self.lineup, pd.DataFrame) and not self.lineup.empty and self.salary > 0

    @property
    def total_salary(self) -> float:
        return float(self.salary)


class LineupOptimizer:
    def __init__(self, salary_cap: int = 50000, objective: str = "cash", risk: float = 0.1):
        self.salary_cap = salary_cap
        self.objective_mode = objective  # 'cash' or 'gpp'
        self.risk_lambda = risk

    # --- Public API (for tests/backwards compatibility) ---
    def optimize(self, df: pd.DataFrame, objective: Optional[str] = None, risk_aversion: Optional[float] = None) -> OptimizeResult:
        if objective:
            self.objective_mode = objective
        if risk_aversion is not None:
            self.risk_lambda = risk_aversion
        return self.run(df)

    def run(self, players: pd.DataFrame) -> OptimizeResult:
        try:
            return self._optimize_lineup(players)
        except Exception as e:
            print(f"[ERROR] Optimizer crash: {e}")
            return self._retry_fallback(players)

    # --- Core optimization ---
    def _optimize_lineup(self, players: pd.DataFrame) -> OptimizeResult:
        # Normalize expected column names (case-insensitive friendly)
        rename_map = {}
        cols_lower = {c.lower(): c for c in players.columns}
        def pick(name): return cols_lower.get(name.lower())

        for src, dst in [("ev","EV"),("sigma","STD"),("salary","Salary"),("position","Pos"),("team","Team")]:
            if pick(src) and pick(src) != dst:
                rename_map[pick(src)] = dst
        players = players.rename(columns=rename_map).copy()

        # Safety: ensure required columns
        required = ["EV","STD","Salary","Pos"]
        for r in required:
            if r not in players.columns:
                raise ValueError(f"Missing required column: {r}")

        # LP model
        model = pulp.LpProblem("DK_Optimizer", pulp.LpMaximize)
        x = {pid: pulp.LpVariable(f"x_{pid}", cat="Binary") for pid in players.index}

        # Objective
        if self.objective_mode == "cash":
            model += pulp.lpSum((players.loc[p, "EV"] - self.risk_lambda * players.loc[p, "STD"]) * x[p] for p in players.index)
        else:  # gpp
            model += pulp.lpSum((players.loc[p, "EV"] + 1.64 * players.loc[p, "STD"]) * x[p] for p in players.index)

        # Constraints
        # Salary cap
        model += pulp.lpSum(players.loc[p, "Salary"] * x[p] for p in players.index) <= self.salary_cap, "salary_cap"
        # Exactly 9 players
        model += pulp.lpSum(x[p] for p in players.index) == 9, "nine_players"
        # Exactly 1 QB and DST
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == "QB") == 1, "one_qb"
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == "DST") == 1, "one_dst"
        # Minimums for RB/WR/TE
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == "RB") >= 2, "min_rb2"
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == "WR") >= 3, "min_wr3"
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == "TE") >= 1, "min_te1"
        # FLEX: exactly seven players must come from RB/WR/TE
        model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] in ("RB","WR","TE")) == 7, "exact_seven_rbwrt"

        # Solve
        status = model.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] != "Optimal":
            print(f"[WARN] LP solver returned {pulp.LpStatus[status]} — triggering structured fallback.")
            return self._retry_fallback(players)

        chosen_ids = [pid for pid in players.index if pulp.value(x[pid]) > 0.5]
        chosen_df = players.loc[chosen_ids].copy().reset_index(drop=True)

        total_salary = float(chosen_df["Salary"].sum())
        total_ev = float(chosen_df["EV"].sum())
        objective_val = float(pulp.value(model.objective))

        # Assign slots, turning the surplus among RB/WR/TE into FLEX
        chosen_df["slot"] = chosen_df["Pos"]
        need = {"RB": 2, "WR": 3, "TE": 1}
        counts = {k: int((chosen_df["Pos"] == k).sum()) for k in need}
        surplus_pos = None
        for k in ("RB","WR","TE"):
            if counts.get(k, 0) > need[k]:
                surplus_pos = k
                break
        if surplus_pos:
            # pick the lowest EV (or highest salary) among surplus to mark FLEX for determinism
            cand = chosen_df[chosen_df["Pos"] == surplus_pos].copy()
            cand = cand.sort_values(["EV","Salary"], ascending=[True, False]).head(1)
            idx_to_flex = cand.index[0]
            chosen_df.loc[idx_to_flex, "slot"] = "FLEX"

        print(f"[INFO] Lineup optimized successfully. Salary: {int(total_salary)}, EV: {total_ev:.2f}")
        return OptimizeResult(lineup=chosen_df, salary=total_salary, ev=total_ev, objective=objective_val)

    # --- Structured fallback (only if LP fails) ---
    def _retry_fallback(self, players: pd.DataFrame) -> OptimizeResult:
        try:
            print("[INFO] Running structured fallback lineup generator.")
            df = players.copy()
            if "ValueRatio" not in df.columns:
                df["ValueRatio"] = df["EV"] / df["Salary"].replace({0: pd.NA})
                df["ValueRatio"] = df["ValueRatio"].fillna(0)

            def top(pos, n):
                return df[df["Pos"] == pos].sort_values(["ValueRatio","EV"], ascending=[False, False]).head(n)

            parts = [
                top("QB",1), top("RB",2), top("WR",3), top("TE",1), top("DST",1)
            ]
            core = pd.concat(parts, ignore_index=True)

            used = set(core.get("name", pd.Series(dtype=str)))
            flex_pool = df[(df["Pos"].isin(["RB","WR","TE"])) & (~df.get("name", pd.Series(dtype=str)).isin(used))]
            flex = flex_pool.sort_values(["ValueRatio","EV"], ascending=[False, False]).head(1)

            lineup_df = pd.concat([core, flex], ignore_index=True).copy()
            lineup_df = lineup_df.head(9).reset_index(drop=True)

            lineup_df["slot"] = lineup_df["Pos"]
            # Mark explicit FLEX (choose among RB/WR/TE surplus)
            need = {"RB":2, "WR":3, "TE":1}
            counts = {k: int((lineup_df["Pos"] == k).sum()) for k in need}
            surplus_pos = None
            for k in ("RB","WR","TE"):
                if counts.get(k, 0) > need[k]:
                    surplus_pos = k
                    break
            if surplus_pos:
                cand = lineup_df[lineup_df["Pos"] == surplus_pos].copy()
                cand = cand.sort_values(["ValueRatio","EV"], ascending=[True, True]).head(1)
                idx_to_flex = cand.index[0]
                lineup_df.loc[idx_to_flex, "slot"] = "FLEX"

            total_salary = float(lineup_df.get("Salary", pd.Series(dtype=float)).sum())
            total_ev = float(lineup_df.get("EV", pd.Series(dtype=float)).sum())
            print(f"[INFO] Structured fallback lineup generated. Players: {len(lineup_df)}, Salary: {int(total_salary)}")
            return OptimizeResult(lineup=lineup_df, salary=total_salary, ev=total_ev, objective=total_ev)
        except Exception as e:
            print(f"[ERROR] Fallback lineup generation failed: {e}")
            return OptimizeResult(lineup=pd.DataFrame(), salary=0, ev=0, objective=0)
