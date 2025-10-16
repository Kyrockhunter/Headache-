
"""
team_simulation.py
Fantasy Simulation Engine v4.1.0
Phase 1: Team-level Monte Carlo Simulation
"""
import logging, numpy as np
from dataclasses import dataclass
from typing import Dict, Any
logger = logging.getLogger(__name__)
class SimulationError(Exception): pass
@dataclass
class TeamStats:
    team: str
    mean_stats: Dict[str, float]
    std_stats: Dict[str, float]
class TeamSimulator:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations
        logger.info("TeamSimulator initialized with %d iterations", iterations)
    def simulate_matchup(self, home: TeamStats, away: TeamStats) -> Dict[str, Any]:
        if not home.mean_stats or not away.mean_stats:
            raise SimulationError(f"Invalid team stats for {home.team} vs {away.team}")
        try:
            results = []
            weights = {"turnovers":0.45,"third_down":0.35,"yards_per_pass":0.30,"first_downs":0.25,"sacks":0.15,"penalties":0.10}
            for _ in range(self.iterations):
                weighted_sum = 0.0
                for stat, w in weights.items():
                    hv = np.random.normal(home.mean_stats.get(stat,0), max(1e-6, home.std_stats.get(stat,1)))
                    av = np.random.normal(away.mean_stats.get(stat,0), max(1e-6, away.std_stats.get(stat,1)))
                    weighted_sum += (hv-av)*w
                results.append(weighted_sum)
            import numpy as _np
            results = _np.array(results)
            win_prob = float((results>0).mean())
            return {"home_team":home.team,"away_team":away.team,"home_win_prob":round(win_prob,3),"iterations":self.iterations}
        except Exception as e:
            logger.exception("Error during matchup simulation: %s", e)
            raise SimulationError(str(e)) from e
