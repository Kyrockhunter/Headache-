"""
player_adjustment.py
-----------------------------------------------------
Fantasy Simulation Engine v4.0.0
Phase 2: Player Context Adjustment Module
-----------------------------------------------------
Adjusts player projections (EV and variance) based on
team simulation results, injury tags, and config weights.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List

import pandas as pd
import numpy as np
import yaml

# Custom exception
class PlayerAdjustmentError(Exception):
    """Raised when player projection adjustment fails."""

# Dataclass for player projections
@dataclass
class PlayerProjection:
    name: str
    team: str
    position: str
    ev_base: float
    sigma_base: float
    injury_status: str = "ACTIVE"

class PlayerAdjuster:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.weights = self.config.get("feature_weights", {})
        self.logger.info("PlayerAdjuster initialized with weights: %s", self.weights)

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.exception("Error loading config: %s", e)
            raise PlayerAdjustmentError(f"Failed to load config: {e}") from e

    def adjust_players(
        self, 
        players: List[PlayerProjection], 
        team_context: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Adjusts each player's EV and sigma based on simulated team stats.
        team_context DataFrame should include:
            columns: ['team', 'yards_per_pass_margin', 'turnover_margin', 'third_down_margin', ...]
        """
        try:
            adjusted = []
            for p in players:
                base_ev = p.ev_base
                base_sigma = p.sigma_base

                # Retrieve team-level stats
                team_row = team_context.loc[team_context["team"] == p.team]
                if team_row.empty:
                    self.logger.warning("No team context found for %s; skipping adjustment", p.name)
                    adj_ev, adj_sigma = base_ev, base_sigma
                else:
                    ctx = team_row.iloc[0]
                    adj_ev, adj_sigma = self._apply_context(p, base_ev, base_sigma, ctx)

                adjusted.append({
                    "name": p.name,
                    "team": p.team,
                    "pos": p.position,
                    "injury_status": p.injury_status,
                    "ev_adj": round(adj_ev, 3),
                    "sigma_adj": round(adj_sigma, 3)
                })

            df = pd.DataFrame(adjusted)
            self.logger.info("Adjusted %d player projections successfully", len(df))
            return df

        except Exception as e:
            self.logger.exception("Error adjusting player projections: %s", e)
            raise PlayerAdjustmentError(f"Player adjustment failed: {e}") from e

    def _apply_context(
        self,
        player: PlayerProjection,
        ev: float,
        sigma: float,
        ctx: pd.Series
    ) -> tuple[float, float]:

        """
        Apply team context-based adjustments to EV and sigma.
        Each position uses different metrics for scaling.
        """
        w = self.weights
        adj_ev = ev
        adj_sigma = sigma

        # Position-specific scaling based on simulated margins
        try:
            if player.position in ["QB", "WR"]:
                adj_ev *= 1 + (ctx.get("yards_per_pass_margin", 0) * w.get("yards_per_pass", 0.001))
                adj_sigma *= 1 + abs(ctx.get("turnover_margin", 0) * 0.01)
            elif player.position == "RB":
                adj_ev *= 1 + (ctx.get("third_down_margin", 0) * w.get("third_down", 0.001))
            elif player.position == "TE":
                adj_ev *= 1 + (ctx.get("first_down_margin", 0) * w.get("first_downs", 0.001))
            elif player.position == "DST":
                adj_ev *= 1 + (ctx.get("turnover_margin", 0) * w.get("turnovers", 0.001))
                adj_sigma *= 1 - abs(ctx.get("sacks_margin", 0) * 0.01)

            # Injury penalty if applicable
            if player.injury_status.upper() in ["Q", "QUESTIONABLE"]:
                adj_ev *= 0.9
                adj_sigma *= 1.15
            elif player.injury_status.upper() in ["O", "OUT"]:
                adj_ev = 0
                adj_sigma = 0

        except Exception as e:
            self.logger.warning("Adjustment failed for %s: %s", player.name, e)

        return adj_ev, adj_sigma
