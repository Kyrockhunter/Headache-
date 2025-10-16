"""
correlated_simulator.py — v4.1.7
Adds p95 column for percentile output.
"""

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


class CorrelatedSimulationError(Exception):
    pass


@dataclass
class PlayerInput:
    name: str
    position: str
    team: str
    ev: float
    sigma: float


class CorrelatedSimulator:
    def __init__(self, iterations: int = 10000):
        self.iterations = iterations
        logger.info("CorrelatedSimulator iterations=%d", iterations)

    def _build_correlation_matrix(self, players: List[PlayerInput]):
        n = len(players)
        corr = np.eye(n)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                pi, pj = players[i], players[j]
                if (pi.position == "QB" and pj.position == "WR") or (pi.position == "WR" and pj.position == "QB"):
                    corr[i, j] = 0.65
                elif (pi.position == "RB" and pj.position == "DST") or (pi.position == "DST" and pj.position == "RB"):
                    corr[i, j] = 0.30
                elif pi.team != pj.team and (
                    (pi.position == "QB" and pj.position == "DST") or (pi.position == "DST" and pj.position == "QB")
                ):
                    corr[i, j] = -0.40
                elif (pi.position == "WR" and pj.position == "TE") or (pi.position == "TE" and pj.position == "WR"):
                    corr[i, j] = -0.10
                else:
                    corr[i, j] = 0.0
        return corr

    def simulate_lineup(self, players: List[PlayerInput]):
        try:
            n = len(players)
            means = np.array([p.ev for p in players])
            sigmas = np.array([p.sigma for p in players])
            corr = self._build_correlation_matrix(players)
            cov = np.outer(sigmas, sigmas) * corr
            cov = (cov + cov.T) / 2

            try:
                L = np.linalg.cholesky(cov + 1e-9 * np.eye(n))
            except np.linalg.LinAlgError:
                eigvals, eigvecs = np.linalg.eigh(cov)
                eigvals[eigvals < 0] = 0
                cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
                L = np.linalg.cholesky(cov + 1e-9 * np.eye(n))

            rng = np.random.default_rng(123)
            z = rng.normal(size=(self.iterations, n))
            totals = (means + (z @ L.T)).sum(axis=1)

            p95_value = np.percentile(totals, 95)
            return pd.DataFrame({
                "lineup_total": totals,
                "mean": [means.mean()] * len(totals),
                "std": [sigmas.mean()] * len(totals),
                "p95": [p95_value] * len(totals)
            })
        except Exception as e:
            logger.exception("Correlated simulation failed: %s", e)
            raise CorrelatedSimulationError(str(e)) from e
