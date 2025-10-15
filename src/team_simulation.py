"""
team_simulation.py
--------------------------------------
Fantasy Football Simulation Engine v4.0.0
Phase 1: Team-level Monte Carlo Simulation
--------------------------------------
Simulates expected win probabilities and key stat margins
(turnovers, yards/pass, 3rd down %, etc.) for each matchup.
"""

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Any

# Custom Exceptions
class SimulationError(Exception):
    """Raised when team simulation fails"""

# Dataclass for team stats
@dataclass
class TeamStats:
    team: str
    mean_stats: Dict[str, float]
    std_stats: Dict[str, float]

# Configure logger
logger = logging.getLogger(__name__)

class TeamSimulator:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations
        logger.info("TeamSimulator initialized with %d iterations", iterations)

    def simulate_matchup(self, home: TeamStats, away: TeamStats) -> Dict[str, Any]:
        """Simulate a matchup between two teams and return win probability and stat margins."""
        try:
            results = []
            for i in range(self.iterations):
                margins = {}
                weighted_sum = 0
                # Feature weights (derived from Roith & Magel)
                weights = {
                    "turnovers": 0.45,
                    "third_down": 0.35,
                    "yards_per_pass": 0.30,
                    "first_downs": 0.25,
                    "sacks": 0.15,
                    "penalties": 0.10
                }

                for stat, w in weights.items():
                    home_val = np.random.normal(home.mean_stats.get(stat, 0), home.std_stats.get(stat, 1))
                    away_val = np.random.normal(away.mean_stats.get(stat, 0), away.std_stats.get(stat, 1))
                    margin = home_val - away_val
                    weighted_sum += margin * w
                    margins[stat] = margin

                results.append(weighted_sum)

            # Compute probabilities
            win_prob = np.mean(np.array(results) > 0)
            avg_margin = {k: np.mean([r for r in results]) for k in ["score"]}
            logger.info("Simulation complete: %s vs %s | Win Prob (Home): %.2f%%", home.team, away.team, win_prob*100)

            return {
                "home_team": home.team,
                "away_team": away.team,
                "home_win_prob": round(win_prob, 3),
                "iterations": self.iterations,
                "feature_margins": avg_margin
            }

        except Exception as e:
            logger.exception("Error during matchup simulation: %s", e)
            raise SimulationError(f"Simulation failed for {home.team} vs {away.team}: {e}") from e

