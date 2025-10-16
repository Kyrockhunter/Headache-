# Fantasy Optimizer — Architecture & Orientation Guide
**Version:** v4.3.1  
**Last updated:** 2025-10-16 02:31  
**Maintained by:** KyRockHunter  
**Python:** 3.13.7

---
## 1) Purpose & Scope
This document explains the system design, module responsibilities, data flow, constraints modeled in the optimizer, and how the simulation and future ML layers connect. It’s written so a **new session or contributor** can quickly regain full context and resume work.

---
## 2) High‑Level Overview
The project builds **DFS lineups** using:
- A **Cleaner** to normalize DraftKings (DK) salary files
- A **Lineup Optimizer** (LP) that enforces classic roster rules (QB, 2 RB, 3 WR, TE, FLEX, DST; salary ≤ 50,000)
- A **Correlated Simulator** to stress‑test lineups and estimate outcome distributions
- A planned **Hybrid Selector** and **Feature Engineering** layer to blend projections, correlations, and expert rules

Target platforms: Windows (CRLF aware) and cross‑platform Python.

---
## 3) Folder Structure
```
fantasy_v4/
├─ data/
│  ├─ raw/                 # Input data (e.g., DKSalaries.csv)
│  └─ outputs/             # Test logs, cleaned CSVs, artifacts
├─ docs/                   # Architecture, changelog, contributing, requirements
├─ src/
│  ├─ cleaner.py           # DK CSV → canonical schema (name, team, position, salary, ev, sigma, game)
│  ├─ optimizer.py         # LP optimizer, FLEX enforcement, result object
│  ├─ correlated_simulator.py # Monte Carlo with correlations; lineup distribution
│  ├─ team_simulation.py   # Team/schedule-level stubs & helpers
│  ├─ hybrid_selector.py   # (Planned) Projection blending, expert heuristics
│  ├─ feature_engineering.py # (Planned) Context features: pace, weather, opponent rank
│  └─ model_training.py    # (Planned) Lightweight ML models (XGBoost/Ridge)
├─ tests/
│  ├─ test_optimizer.py    # Optimizer validity & slot checks
│  ├─ test_correlated_simulator.py
│  └─ test_team_simulation.py
└─ run_framework_tests.py  # CI-like runner; pytest + E2E + logs
```

---
## 4) Data Contracts
**Cleaner output columns** (canonical schema):
- `name: str`, `team: str`, `position: str`, `salary: int`, `ev: float`, `sigma: float`, `game: str`
- Additional derived: `ValueRatio = ev / salary` (when needed)

**Optimizer input** must include (any case accepted, normalized internally):
- `EV`, `STD`, `Salary`, `Pos`, optional `Team`, `name`
- Optimizer normalizes case and aliases (e.g., `ev`→`EV`).

---
## 5) Optimizer (LP/MILP) — Core Logic
**Objective modes**
- **cash:** maximize `Σ (EV - λ·STD)`
- **gpp:**  maximize `Σ (EV + 1.64·STD)`
  - `λ` is risk‐aversion; configurable.

**Constraints (Classic DK 9‑man)**
- Salary cap: `Σ Salary·x ≤ 50,000`
- Roster size: `Σ x = 9`
- Uniques: binary decision variable per player
- Positional hard requirements:
  - `QB == 1`, `DST == 1`
  - `RB ≥ 2`, `WR ≥ 3`, `TE ≥ 1`
  - **FLEX enforcement:** `Σ x_{{RB,WR,TE}} == 7`  ← guarantees exactly one FLEX among RB/WR/TE
- Solver: PuLP (CBC). Fallback is a **structured heuristic** that still assigns FLEX explicitly.

**Post‑processing**
- Default slot = `Pos`
- Surplus among {{RB, WR, TE}} is relabeled to `FLEX` (deterministic choice).  
- Result packaged as `OptimizeResult(lineup: pd.DataFrame, salary, ev, objective, total_salary@property)`.

---
## 6) Correlated Simulator — Summary
- Inputs: list of `PlayerInput(name, position, team, ev, sigma)`
- Process: Monte Carlo iterations (configurable), optional correlation matrix (team/game)
- Output DataFrame includes: `lineup_total` (+ optional `mean`, `std`, `p95` depending on run/setups)
- Use cases: smoke‑test lineups, compare EV vs tail risk, GPP ceiling ranking

---
## 7) Test & Run Pipeline
- **Unit tests**: `pytest -q` (see `/tests`)
- **Integrated test runner**: `python run_framework_tests.py`
  - Writes logs to `data/outputs/test_summary_<timestamp>.txt`
  - Cleans DK file (from `data/raw/`) → builds lineup → validates roster → simulation smoke test

---
## 8) Planned Modules (Roadmap)
- `feature_engineering.py`: rolling windows, opponent rank vs. position, pace, weather, Vegas implied totals, correlation metrics
- `hybrid_selector.py`: projection blending (weights, Bayesian adjustments), correlation & ownership heuristics → adjusted EV
- `model_training.py`: optional ML regressors for EV tuning; export `model.joblib`

---
## 9) Config & Environment
- Python 3.13.7
- Install: `pip install -r docs/requirements.txt`
- Windows line endings: Git may convert LF↔CRLF; safe to ignore warning or set `core.autocrlf=true`
- Paths: `src/` is import root; runner ensures `sys.path` includes project root

---
## 10) Logging & Artifacts
- Test logs and cleaned CSVs: `/data/outputs/`
- Raw DK input: `/data/raw/`
- Recommended to keep weekly snapshots for reproducibility (date‑stamped CSVs)

---
## 11) Contribution and Versioning
- Semantic Versioning: `MAJOR.MINOR.PATCH` (e.g., v4.3.1)
- Typical commit: `feat(optimizer): FLEX modeling and constraints (v4.3.1)`
- Tag releases: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- See `CONTRIBUTING.md` for detailed workflow

---
## 12) Quick Start
```bash
# Install
pip install -r docs/requirements.txt

# Run tests
pytest -q

# End‑to‑end runner (pytest + lineup + logs)
python run_framework_tests.py
```

---
## Appendix — Glossary
- **EV**: Expected fantasy points
- **STD**: Standard deviation (risk proxy)
- **FLEX**: Roster slot eligible for RB/WR/TE
- **GPP**: Tournaments; prefer ceiling and correlation
- **Cash**: Head‑to‑head/50‑50; prefer safety/consistency
