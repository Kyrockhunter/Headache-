#!/usr/bin/env python3
"""
Fantasy Optimizer – Framework Test Runner (v4.3.0)
Maintained by: KyRockHunter
Python: 3.13.7

What this script does:
  1) Runs ALL pytest tests and captures FULL output to a timestamped log.
  2) Attempts an end-to-end check using your DK salaries file from data/raw/:
       - Cleans DK CSV -> canonical schema (via cleaner module if available)
       - Builds a lineup via LineupOptimizer (or heuristic fallback)
       - Validates roster (9 players, salary <= 50000, slot coverage)
       - Runs a small simulation smoke test
  3) Prints colorized console summary and writes a detailed report to data/outputs/.
"""
import sys
import subprocess
import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd  # ensure pd is defined

# Color output (safe fallback if colorama missing)
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:
    class Dummy:
        RESET_ALL = ""
        GREEN = ""
        RED = ""
        YELLOW = ""
        CYAN = ""
        MAGENTA = ""
    Fore = Style = Dummy()

def c_ok(msg): print(f"{Fore.GREEN}✔ {msg}{Style.RESET_ALL}")
def c_warn(msg): print(f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")
def c_err(msg): print(f"{Fore.RED}✘ {msg}{Style.RESET_ALL}")
def c_info(msg): print(f"{Fore.CYAN}• {msg}{Style.RESET_ALL}")

ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
OUTPUTS = ROOT / "data" / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

# Ensure project root is importable (so "src" and root modules resolve in VS Code & runtime)
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
LOG = OUTPUTS / f"test_summary_{TS}.txt"

# ---------------- PyTest Runner ----------------
def run_pytest() -> Tuple[int, str]:
    """Run pytest as a subprocess, tee stdout/stderr to console and capture to string."""
    c_info("Running pytest (full output will be logged)...")
    cmd = [sys.executable, "-m", "pytest", "-vv"]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    output_lines = []
    for line in proc.stdout:
        print(line, end="")  # live echo
        output_lines.append(line)
    proc.wait()
    return proc.returncode, "".join(output_lines)

# ---------------- Data Cleaning ----------------
def clean_dk_if_available() -> Optional[pd.DataFrame]:
    """If DK CSV exists under data/raw, run cleaner; else return None. Falls back to inline mapping."""
    dk = None
    for fname in ["DKSalaries.csv", "DKSalaries (3).csv", "DKSalaries (2).csv"]:
        cand = DATA_RAW / fname
        if cand.exists():
            dk = cand
            break
    if dk is None:
        c_warn("DK salaries file not found in ./data/raw — skipping end-to-end lineup check.")
        return None

    # Try project cleaner first: src.cleaner or cleaner in project root
    try:
        try:
            from src.cleaner import clean_dk_file  # type: ignore
            c_info(f"Cleaning DK file via src.cleaner: {dk.name}")
        except Exception:
            from cleaner import clean_dk_file  # type: ignore
            c_info(f"Cleaning DK file via cleaner.py: {dk.name}")
        cleaned_path = OUTPUTS / f"cleaned_players_{TS}.csv"
        df = clean_dk_file(str(dk), str(cleaned_path))
        return df
    except Exception as e:
        c_warn(f"Cleaner import failed ({e}); attempting inline mapping...")

    # Inline fallback cleaner
    try:
        c_info(f"Cleaning DK file inline: {dk.name}")
        raw = pd.read_csv(dk)
        # DK classic columns commonly present:
        candidates = [
            ("Name", "TeamAbbrev", "Position", "Salary", "AvgPointsPerGame", "Game Info"),
            ("Name", "Team", "Position", "Salary", "AvgPointsPerGame", "Game Info"),
        ]
        cols = None
        for tpl in candidates:
            if all(col in raw.columns for col in tpl):
                cols = tpl
                break
        if cols is None:
            raise RuntimeError("Could not find expected DK column set in CSV.")
        df = raw[list(cols)].copy()
        df.columns = ["name", "team", "position", "salary", "ev", "game"]
        # Risk heuristic: sigma = 0.2 * ev (if not provided elsewhere)
        df["sigma"] = df["ev"].fillna(0.0) * 0.2
        # Ensure numeric salary
        df["salary"] = pd.to_numeric(df["salary"], errors="coerce").fillna(0).astype(int)
        # Deduplicate
        df.drop_duplicates(subset=["name", "team", "position"], inplace=True)
        cleaned_path = OUTPUTS / f"cleaned_players_{TS}.csv"
        df.to_csv(cleaned_path, index=False)
        return df
    except Exception as e:
        c_err(f"Inline cleaning failed: {e}")
        return None

# ---------------- Lineup Validation ----------------
def validate_lineup(df_lineup: pd.DataFrame) -> Tuple[bool, list]:
    """Validate classic roster rules and salary cap. Return (ok, messages)."""
    msgs = []
    ok = True
    lu = df_lineup.copy()
    # Normalize columns
    if "slot" not in lu.columns and "Pos" in lu.columns:
        lu["slot"] = lu["Pos"]
    if "Salary" in lu.columns and "salary" not in lu.columns:
        lu["salary"] = lu["Salary"]
    if "position" not in lu.columns and "Pos" in lu.columns:
        lu["position"] = lu["Pos"]

    # Count / constraints
    if len(lu) != 9:
        ok = False
        msgs.append(f"Expected 9 players, got {len(lu)}")
    total_salary = int(lu.get("salary", 0).sum())
    if total_salary > 50000:
        ok = False
        msgs.append(f"Salary cap exceeded: {total_salary} > 50000")
    # Slot/position checks
    pos = lu.get("position")
    slot = lu.get("slot", pos)
    if pos is None and slot is None:
        msgs.append("No position/slot columns found")
        ok = False
    else:
        p = (pos if pos is not None else slot)
        def cnt(name): return int((p == name).sum())
        reqs = [("QB",1),("RB",2),("WR",3),("TE",1)]
        for k,need in reqs:
            have = cnt(k)
            if have < need:
                ok = False
                msgs.append(f"Need at least {need} {k}, found {have}")
        # FLEX implicit check: extra RB/WR/TE beyond required totals
        extra = cnt("RB") + cnt("WR") + cnt("TE") - (2+3+1)
        if extra < 1:
            msgs.append("No FLEX (RB/WR/TE) detected; expected one extra among RB/WR/TE.")
            ok = False
    return ok, msgs

# ---------------- End-to-End Lineup Build ----------------
def build_lineup_end_to_end(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Try to build a lineup using LineupOptimizer; fallback to heuristic if needed."""
    lineup = None
    # Attempt optimizer from src
    try:
        from src.optimizer import LineupOptimizer  # type: ignore
        c_info("Building lineup via src.optimizer.LineupOptimizer (gpp objective).")
        opt = LineupOptimizer(salary_cap=50000)
        res = None
        try:
            res = opt.optimize(df, objective="gpp")
        except Exception:
            # Some versions used run()
            res = opt.run(df)
        lineup = getattr(res, "lineup", None) or None
        if lineup is None or len(lineup) == 0:
            raise RuntimeError("Optimizer returned empty lineup.")
        return lineup
    except Exception as e:
        c_warn(f"Optimizer run failed: {e}")

    # Heuristic fallback
    try:
        import numpy as np
        pool = df.copy()
        pool["ValueRatio"] = pool["ev"] / pool["salary"].replace({0: np.nan})
        qb = pool[pool["position"]=="QB"].sort_values("ValueRatio", ascending=False).head(1)
        rb = pool[pool["position"]=="RB"].sort_values("ValueRatio", ascending=False).head(5)
        wr = pool[pool["position"]=="WR"].sort_values("ValueRatio", ascending=False).head(7)
        te = pool[pool["position"]=="TE"].sort_values("ValueRatio", ascending=False).head(3)
        dst = pool[pool["position"]=="DST"].sort_values("ValueRatio", ascending=False).head(2)
        parts = [qb.head(1), rb.head(2), wr.head(3), te.head(1), dst.head(1)]
        core = pd.concat(parts, ignore_index=True)
        used = set(core["name"])
        flex_pool = pool[pool["position"].isin(["RB","WR","TE"]) & (~pool["name"].isin(used))]
        flex = flex_pool.sort_values("ValueRatio", ascending=False).head(1)
        lineup = pd.concat([core, flex], ignore_index=True)
        lineup["slot"] = lineup["position"]
        c_info("Used heuristic fallback lineup.")
        return lineup
    except Exception as e2:
        c_err(f"Heuristic fallback failed: {e2}")
        return None

# ---------------- Simulation Smoke Test ----------------
def simulate_lineup_smoke(lineup: pd.DataFrame) -> bool:
    """Run a small correlated simulation to ensure simulator works."""
    try:
        from src.correlated_simulator import CorrelatedSimulator, PlayerInput  # type: ignore
    except Exception as e:
        c_warn(f"Simulator import failed or missing: {e}")
        return False

    try:
        sim = CorrelatedSimulator(iterations=1000)
        pins = [
            PlayerInput(
                name=str(r["name"]),
                position=str(r["position"]),
                team=str(r.get("team", "")),
                ev=float(r["ev"]),
                sigma=float(r["sigma"]),
            )
            for _, r in lineup.iterrows()
        ]
        df = sim.simulate_lineup(pins)
        if "lineup_total" not in df.columns:
            c_warn("Simulator output missing 'lineup_total'.")
            return False
        c_ok("Simulator smoke test succeeded.")
        return True
    except Exception as e:
        c_warn(f"Simulation failed: {e}")
        return False

# ---------------- Main ----------------
def main():
    print("="*74)
    print(" FANTASY OPTIMIZER – FRAMEWORK TEST (v4.3.0) ".center(74, "="))
    print("="*74)

    code, out = run_pytest()
    with open(LOG, "w", encoding="utf-8") as f:
        f.write(out)

    if code == 0:
        c_ok("All pytest tests passed.")
    else:
        c_err("Some pytest tests failed. See log for details: " + str(LOG))

    # End-to-end
    df = clean_dk_if_available()
    e2e_ok = True
    if df is not None and not df.empty:
        lineup = build_lineup_end_to_end(df)
        if lineup is None or lineup.empty:
            c_err("Failed to build any lineup.")
            e2e_ok = False
        else:
            ok, msgs = validate_lineup(lineup)
            if ok:
                c_ok("Lineup integrity validated (9 players, salary <= 50000, slots present).")
            else:
                c_err("Lineup validation failed:")
                for m in msgs:
                    c_err("  - " + m)
                e2e_ok = False
            # Simulation smoke
            sim_ok = simulate_lineup_smoke(lineup)
            if not sim_ok:
                c_warn("Simulation smoke test did not complete successfully.")
    else:
        c_warn("No DK data available; skipped end-to-end lineup test.")

    print("-"*74)
    if code == 0 and e2e_ok:
        c_ok("FRAMEWORK STATUS: STABLE ✅")
        rc = 0
    else:
        c_err("FRAMEWORK STATUS: ATTENTION REQUIRED ❌")
        rc = 1

    print(f"Full pytest log saved to: {LOG}")
    print("="*74)
    sys.exit(rc)

if __name__ == "__main__":
    main()
