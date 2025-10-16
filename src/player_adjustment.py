
"""
player_adjustment.py
Fantasy Simulation Engine v4.1.0
Phase 2: Player Context Adjustment
"""
import logging
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
logger = logging.getLogger(__name__)
class PlayerAdjustmentError(Exception): pass
@dataclass
class PlayerProjection:
    name: str; team: str; position: str; ev_base: float; sigma_base: float; injury_status: str = "ACTIVE"
class PlayerAdjuster:
    def __init__(self, weights: Dict[str, float] | None = None):
        self.weights = weights or {"turnovers":0.001,"third_down":0.001,"yards_per_pass":0.001,"first_downs":0.001,"sacks":0.001}
        logger.info("PlayerAdjuster initialized with weights: %s", self.weights)
    def adjust_players(self, players: List[PlayerProjection], team_context: pd.DataFrame) -> pd.DataFrame:
        try:
            rows = []
            for p in players:
                ev = float(p.ev_base); sig = float(p.sigma_base)
                ctx = team_context[team_context["team"]==p.team]
                if not ctx.empty:
                    c = ctx.iloc[0]
                    if p.position in ("QB","WR"): ev *= 1 + c.get("yards_per_pass_margin",0)*self.weights["yards_per_pass"]
                    if p.position=="RB": ev *= 1 + c.get("third_down_margin",0)*self.weights["third_down"]
                    if p.position=="TE": ev *= 1 + c.get("first_down_margin",0)*self.weights["first_downs"]
                    if p.position=="DST": ev *= 1 + c.get("turnover_margin",0)*self.weights["turnovers"]
                if str(p.injury_status).upper() in ("Q","QUESTIONABLE"): ev *= 0.9; sig *= 1.15
                elif str(p.injury_status).upper() in ("O","OUT"): ev = 0.0; sig = 0.0
                rows.append({"name":p.name,"team":p.team,"position":p.position,"ev":round(ev,3),"sigma":round(sig,3)})
            return pd.DataFrame(rows)
        except Exception as e:
            logger.exception("Adjustment failed: %s", e); raise PlayerAdjustmentError(str(e)) from e
