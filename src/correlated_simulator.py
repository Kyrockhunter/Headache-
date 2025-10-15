"""
correlated_simulator.py
-----------------------------------------------------
Fantasy Simulation Engine v4.0.0
Phase 3: Correlated Monte Carlo Simulation Layer
-----------------------------------------------------
Generates multivariate fantasy outcomes for a lineup
based on player projection means, variances, and
cross-player correlations (e.g., QB↔WR, RB↔DST).
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import yaml

# ---------------------------------------------------
# Custom Exception
# ---------------------------------------------------
class CorrelatedSimulationError(Exception):
    """Raised when correlated Monte Carlo simulation fails."""

# ---------------------------------------------------
# Dataclass for Player
# ---------------------------------------------------
@dataclass
class PlayerInput:
    name: str
    position: str
    team: str
    ev: float
    sigma: float

# ---------------------------------------------------
# Correlated Simulator
# ---------------------------------------------------
class CorrelatedSimulator:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.iterations = self.config.get("simulation", {}).get("iterations", 10000)
        self.logger.info("CorrelatedSimulator initialized with %d iterations", self.iterations)

    # ---------------------------------------------------
    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration."""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.exception("Error loading config: %s", e)
            raise CorrelatedSimulationError(f"Failed to load config: {e}") from e

    # ---------------------------------------------------
    def _build_correlation_matrix(self, players: List[PlayerInput]) -> np.ndarray:
        """
        Build a simple position-based correlation matrix.
        Positive correlations improve realism for stacks.
        """
        n = len(players)
        corr = np.identity(n)

        # basic correlation rules
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                pi, pj = players[i], players[j]

                # QB ↔ WR: strong positive correlation
                if (pi.position == "QB" and pj.position == "WR") or (pi.position == "WR" and pj.position == "QB"):
                    corr[i, j] = 0.65
                # RB ↔ DST: moderate positive correlation
                elif (pi.position == "RB" and pj.position == "DST") or (pi.position == "DST" and pj.position == "RB"):
                    corr[i, j] = 0.30
                # Opposing QB ↔ DST: negative correlation
                elif pi.team != pj.team and ((pi.position == "QB" and pj.position == "DST") or (pi.position == "DST" and pj.position == "QB")):
                    corr[i, j] = -0.40
                # WR ↔ TE slight negative (target share)
                elif (pi.position == "WR" and pj.position == "TE") or (pi.position == "TE" and pj.position == "WR"):
                    corr[i, j] = -0.10
                else:
                    corr[i, j] = 0.0
        return corr

    # ---------------------------------------------------
    def simulate_lineup(self, players: List[PlayerInput]) -> pd.DataFrame:
        """
        Run correlated Monte Carlo simulation for a single lineup.
        Returns DataFrame of total scores for each iteration.
        """
        try:
            n = len(players)
            means = np.array([p.ev for p in players])
            sigmas = np.array([p.sigma for p in players])
            corr = self._build_correlation_matrix(players)

            # ensure positive semi-definite covariance matrix
            cov = np.outer(sigmas, sigmas) * corr
            cov = (cov + cov.T) / 2  # symmetrize

            # Cholesky may fail if not PSD, so fall back gracefully
            try:
                L = np.linalg.cholesky(cov)
            except np.linalg.LinAlgError:
                self.logger.warning("Covariance not PSD, using np.linalg.eigh fix.")
                eigvals, eigvecs = np.linalg.eigh(cov)
                eigvals[eigvals < 0] = 0
                cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
                L = np.linalg.cholesky(cov + 1e-8 * np.eye(n))

            rng = np.random.default_rng(123)
            z = rng.normal(size=(self.iterations, n))
            correlated = z @ L.T
            simulated = means + correlated

            totals = simulated.sum(axis=1)
            df = pd.DataFrame({
                "iteration": np.arange(self.iterations),
                "lineup_total": totals
            })
            df["mean"] = totals.mean()
            df["std"] = totals.std()
            df["p95"] = np.percentile(totals, 95)
            self.logger.info("Simulated %d iterations; mean=%.2f, p95=%.2f",
                             self.iterations, df['mean'].iloc[0], df['p95'].iloc[0])
            return df

        except Exception as e:
            self.logger.exception("Simulation failed: %s", e)
            raise CorrelatedSimulationError(f"Simulation failed: {e}") from e
