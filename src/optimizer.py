"""
optimizer.py — v4.2.3
Classic 9-man lineup logic (QB, 2 RB, 3 WR, TE, FLEX, DST).
FLEX can be RB/WR/TE regardless of main slot counts.
"""

import pulp
import pandas as pd
from dataclasses import dataclass
from typing import List


@dataclass
class OptimizeResult:
    lineup: pd.DataFrame
    salary: float
    ev: float
    objective: float

    def is_valid(self):
        return not self.lineup.empty and self.salary > 0

    @property
    def total_salary(self):
        return self.salary


class LineupOptimizer:
    def __init__(self, salary_cap: int = 50000, objective: str = "cash", risk: float = 0.1):
        self.salary_cap = salary_cap
        self.objective_mode = objective
        self.risk_lambda = risk

    def optimize_lineup(self, players: pd.DataFrame) -> OptimizeResult:
        try:
            players = players.rename(columns={
                "ev": "EV",
                "sigma": "STD",
                "salary": "Salary",
                "position": "Pos",
                "team": "Team"
            })

            model = pulp.LpProblem("DK_Optimizer", pulp.LpMaximize)
            x = {pid: pulp.LpVariable(f"x_{pid}", cat="Binary") for pid in players.index}

            if self.objective_mode == "cash":
                model += pulp.lpSum(
                    (players.loc[p, "EV"] - self.risk_lambda * players.loc[p, "STD"]) * x[p]
                    for p in players.index
                )
            else:
                model += pulp.lpSum(
                    (players.loc[p, "EV"] + 1.64 * players.loc[p, "STD"]) * x[p]
                    for p in players.index
                )

            model += pulp.lpSum(players.loc[p, "Salary"] * x[p] for p in players.index) <= self.salary_cap
            model += pulp.lpSum(x[p] for p in players.index) == 9

            for pos, limit in {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "DST": 1}.items():
                model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] == pos) == limit

            model += pulp.lpSum(x[p] for p in players.index if players.loc[p, "Pos"] in ["RB", "WR", "TE"]) >= 6

            status = model.solve(pulp.PULP_CBC_CMD(msg=False))
            if pulp.LpStatus[status] != "Optimal":
                print(f"[WARN] LP solver returned {pulp.LpStatus[status]} — triggering structured fallback.")
                return self.retry_fallback(players)

            chosen_df = players[[x[p].value() == 1 for p in players.index]].copy()
            total_salary = chosen_df["Salary"].sum()
            total_ev = chosen_df["EV"].sum()
            objective_val = pulp.value(model.objective)

            chosen_df["slot"] = chosen_df["Pos"]

            print(f"[INFO] Lineup optimized successfully. Salary: {total_salary}, EV: {total_ev}")
            return OptimizeResult(
                lineup=chosen_df,
                salary=total_salary,
                ev=total_ev,
                objective=objective_val,
            )
        except Exception as e:
            print(f"[ERROR] Optimizer crash: {e}")
            return self.retry_fallback(players)

    def retry_fallback(self, players: pd.DataFrame) -> OptimizeResult:
        """Structured fallback: Classic 9-man lineup with FLEX = RB/WR/TE."""
        try:
            print("[INFO] Running structured fallback lineup generator.")
            players["ValueRatio"] = players["EV"] / players["Salary"]
            sorted_players = players.sort_values("ValueRatio", ascending=False)

            lineup = []
            total_salary = 0

            def pick_position(pos, count):
                nonlocal total_salary
                selected = sorted_players[sorted_players["Pos"] == pos].head(count)
                for _, p in selected.iterrows():
                    if total_salary + p["Salary"] <= self.salary_cap + 200:
                        lineup.append(p.to_dict())
                        total_salary += p["Salary"]

            # Required slots
            pick_position("QB", 1)
            pick_position("RB", 2)
            pick_position("WR", 3)
            pick_position("TE", 1)
            pick_position("DST", 1)

            # FLEX (RB/WR/TE regardless of previous counts)
            used_names = {p["name"] for p in lineup}
            remaining = sorted_players[
                (sorted_players["Pos"].isin(["RB", "WR", "TE"])) & (~sorted_players["name"].isin(used_names))
            ].copy()

            if not remaining.empty:
                flex_pick = remaining.sort_values("ValueRatio", ascending=False).head(1)
                p = flex_pick.iloc[0]
                if total_salary + p["Salary"] <= self.salary_cap + 200:
                    lineup.append(p.to_dict())
                    total_salary += p["Salary"]

            lineup_df = pd.DataFrame(lineup)
            lineup_df["slot"] = lineup_df.get("Pos", None)
            total_ev = lineup_df["EV"].sum() if not lineup_df.empty else 0

            # Ensure exactly 9 players
            if len(lineup_df) < 9:
                filler = sorted_players.head(9 - len(lineup_df))
                lineup_df = pd.concat([lineup_df, filler])

            lineup_df = lineup_df.head(9).reset_index(drop=True)
            print(f"[INFO] Structured fallback lineup generated. Players: {len(lineup_df)}, Salary: {total_salary}")
            return OptimizeResult(lineup=lineup_df, salary=total_salary, ev=total_ev, objective=total_ev)

        except Exception as e:
            print(f"[ERROR] Fallback lineup generation failed: {e}")
            return OptimizeResult(lineup=pd.DataFrame(), salary=0, ev=0, objective=0)

    def run(self, players: pd.DataFrame) -> OptimizeResult:
        result = self.optimize_lineup(players)
        if not isinstance(result, OptimizeResult) or not result.is_valid():
            print("[WARN] No valid lineup — returning empty OptimizeResult.")
            return OptimizeResult(lineup=pd.DataFrame(), salary=0, ev=0, objective=0)
        return result

    def optimize(self, df, objective=None, risk_aversion=None):
        if objective:
            self.objective_mode = objective
        if risk_aversion is not None:
            self.risk_lambda = risk_aversion
        return self.run(df)
