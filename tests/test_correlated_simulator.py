"""
Unit tests for correlated_simulator.py
Phase 3: Correlated Monte Carlo Simulation Layer
"""

import pytest
import pandas as pd
from src.correlated_simulator import CorrelatedSimulator, PlayerInput, CorrelatedSimulationError


def test_simulation_runs_and_outputs_dataframe():
    """Test that simulator runs and returns a DataFrame with expected columns."""
    players = [
        PlayerInput("P. Mahomes", "QB", "KC", 22.0, 5.0),
        PlayerInput("T. Kelce", "TE", "KC", 18.0, 4.0),
        PlayerInput("I. Pacheco", "RB", "KC", 15.0, 3.5),
        PlayerInput("KC Defense", "DST", "KC", 8.0, 2.0)
    ]

    sim = CorrelatedSimulator()
    df = sim.simulate_lineup(players)

    # Basic output validation
    assert isinstance(df, pd.DataFrame)
    assert "lineup_total" in df.columns
    assert "mean" in df.columns
    assert "std" in df.columns
    assert "p95" in df.columns

    # Logical sanity checks
    assert df["lineup_total"].mean() > 0
    assert df["std"].iloc[0] > 0


def test_invalid_input_raises_error(monkeypatch):
    """Ensure simulation raises CorrelatedSimulationError for invalid data."""
    bad_players = [PlayerInput("X", "QB", "KC", 0, 0)]
    sim = CorrelatedSimulator()

    # Patch internal function to force an error
    def bad_cov(*args, **kwargs):
        raise ValueError("Bad covariance")
    monkeypatch.setattr(sim, "_build_correlation_matrix", bad_cov)

    with pytest.raises(CorrelatedSimulationError):
        sim.simulate_lineup(bad_players)
