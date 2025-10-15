"""
Unit tests for team_simulation.py
"""

import pytest
import numpy as np
from src.team_simulation import TeamSimulator, TeamStats, SimulationError

def test_basic_simulation_runs():
    """Ensure simulation produces win probability output."""
    home = TeamStats("KC", 
                     mean_stats={"turnovers": 1.0, "third_down": 45.0, "yards_per_pass": 7.5,
                                 "first_downs": 22.0, "sacks": 2.0, "penalties": 5.0},
                     std_stats={"turnovers": 0.5, "third_down": 5.0, "yards_per_pass": 1.0,
                                "first_downs": 3.0, "sacks": 1.0, "penalties": 1.0})
    away = TeamStats("BUF", 
                     mean_stats={"turnovers": 1.2, "third_down": 43.0, "yards_per_pass": 6.8,
                                 "first_downs": 21.0, "sacks": 2.2, "penalties": 6.0},
                     std_stats={"turnovers": 0.4, "third_down": 4.0, "yards_per_pass": 0.8,
                                "first_downs": 2.0, "sacks": 1.0, "penalties": 1.0})
    sim = TeamSimulator(iterations=5000)
    result = sim.simulate_matchup(home, away)
    assert "home_win_prob" in result
    assert 0 <= result["home_win_prob"] <= 1

def test_invalid_input_raises():
    """Ensure invalid inputs raise SimulationError."""
    sim = TeamSimulator(iterations=100)
    bad = TeamStats("X", {}, {})
    with pytest.raises(SimulationError):
        sim.simulate_matchup(bad, bad)
