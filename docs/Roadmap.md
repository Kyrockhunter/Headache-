# Fantasy Optimizer Development Roadmap
### Generated: 2025-10-16 02:29:27
---
## Phase 1 — Advanced Scoring Prediction Overview
Goal: Extend the lineup optimizer beyond static projections to include contextual, correlation-based, and AI‑driven prediction.

**Current (v4.3.x)**: Stable optimizer with FLEX constraint modeling and fallback safety.

### Next steps:
1. Integrate hybrid projection blending.
2. Add correlated player simulation (Monte Carlo).
3. Introduce feature engineering pipeline.
4. Support optional ML models for projection tuning.

---
## Phase 2 — Architecture Plan
```
src/
├── optimizer.py
├── correlated_simulator.py
├── team_simulation.py
├── cleaner.py
├── hybrid_selector.py     ← NEW
├── feature_engineering.py ← NEW
└── model_training.py      ← NEW
```
---
### 1. feature_engineering.py
- Rolling averages, opponent rank, team total, weather, pace.
- Correlation metrics (QB→WR, RB→OL, DEF→RB).

### 2. hybrid_selector.py
- Weighted projection blending across sources.
- Bayesian and correlation adjustments.
- Output: adjusted EV per player.

### 3. correlated_simulator.py
- Monte Carlo simulations with covariance matrix.
- Compute mean, std, p95, boom/bust probabilities.

### 4. model_training.py
- Optional ML model training (XGBoost/CatBoost/Ridge).
- Output: model.joblib for runtime use.

### 5. optimizer.py Integration
- Preprocess using hybrid_selector before LP optimization.

---
## Phase 3 — Simulation & Evaluation Layer
- Run thousands of simulated slates.
- Measure lineup distribution, variance, and stability.
- Rank lineups by ROI and win probability.

---
## Phase 4 — Continuous Improvement
- Weekly accuracy audits.
- Progressive model retraining.
- Streamlit dashboard for trend visualization.
