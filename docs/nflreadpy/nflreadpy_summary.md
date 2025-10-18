# nflreadpy Summary Report

## Overview
`nflreadpy` is a Python port of the R package `nflreadr`, providing access to NFL data from the nflverse repositories. It focuses on clean, fast data ingestion and uses the Polars library for improved performance.

## Key Features
- Compatible with R’s nflreadr API
- Uses Polars DataFrames
- Built-in caching (memory/filesystem)
- Progress tracking
- Configurable behavior (cache, verbosity, timeout)
- Pulls data from nflverse and dynastyprocess repositories

## Common Functions and Usage

| Function | Description | Example |
|-----------|--------------|---------|
| `load_pbp()` | Load play-by-play data | `nfl.load_pbp([2023])` |
| `load_player_stats()` | Load player-level stats | `nfl.load_player_stats([2022, 2023])` |
| `load_team_stats()` | Load team stats | `nfl.load_team_stats([2023])` |
| `load_rosters()` | Load team rosters | `nfl.load_rosters()` |
| `load_schedules()` | Load schedule data | `nfl.load_schedules()` |
| `load_injuries()` | Load injury reports | `nfl.load_injuries([2024])` |
| `clear_cache()` | Clear cached data | `nfl.clear_cache()` |
| `get_current_season()` | Current season | `nfl.get_current_season()` |
| `get_current_week()` | Current week | `nfl.get_current_week()` |

## Configuration Example
```python
from nflreadpy.config import update_config
update_config(
    cache_mode="filesystem",
    verbose=True,
    prefer_format="parquet"
)
```

## Sample Data Workflow
```python
import nflreadpy as nfl
from nflreadpy.config import update_config

update_config(cache_mode="filesystem", verbose=True)
pbp = nfl.load_pbp([2023])
stats = nfl.load_player_stats([2022, 2023])
rosters = nfl.load_rosters()
merged = stats.join(rosters, on="player_id", how="left")
```

## Strengths
- Fast Polars backend
- Community-standard data
- Modular and flexible
- Cross-language compatible

## Limitations
- Relies on upstream data freshness
- Possible memory overhead when converting to pandas
- Must manage cache invalidation

## Recommended Use in FantasyV4
Use `nflreadpy` for:
- Weekly player performance data
- Team schedules and matchups
- Injury and roster information
- Integrating with feature engineering modules

