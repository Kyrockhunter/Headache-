#!/usr/bin/env python
"""
FantasyV4 Tool: build_week_via_master.py
----------------------------------------
Tiny wrapper that delegates week/year builds to the *working* weekly_master module.
- Accepts --season and --week (or prompts interactively)
- Imports and calls your existing weekly master builder directly
- Optional --append triggers historical_merge to refresh season master
- Robust import path discovery: tries common module paths used in FantasyV4
"""

import argparse
import sys
import os
from importlib import import_module
from datetime import datetime

def resolve_weekly_master():
    """Try multiple import paths to find the working weekly_master module."""
    candidates = [
        "src.data_builder.weekly_master",
        "src.features.weekly_master",
        "src.weekly_master",
        "tools.weekly_master",
        "weekly_master",
    ]
    last_err = None
    for modname in candidates:
        try:
            return import_module(modname)
        except Exception as e:
            last_err = e
            continue
    raise ImportError(f"Could not import weekly_master. Last error: {last_err}")

def call_builder(mod, season: int, week: int):
    """
    Call the most likely entry point exposed by your weekly_master.
    Supported names it will try in order:
      - build_weekly_master(season=..., week=...)
      - run(season=..., week=...)
      - main(season=..., week=...)
    If none exist, it will exit with a clear message.
    """
    for fname in ("build_weekly_master", "run", "main"):
        fn = getattr(mod, fname, None)
        if callable(fn):
            try:
                return fn(season=season, week=week)
            except TypeError:
                # Some implementations may use positional args
                return fn(season, week)
            except Exception as e:
                print(f"❌ weekly_master.{fname} raised: {e}")
                raise

    # If we get here, no function was found
    names = [n for n in dir(mod) if not n.startswith("_")]
    raise AttributeError(
        "weekly_master module does not expose a callable builder.\n"
        "Expected one of: build_weekly_master, run, main.\n"
        f"Exported names: {names[:25]}..."
    )

def historical_append(season: int):
    """Optionally refresh season master by calling tools.historical_merge.merge_season."""
    try:
        hm = import_module("tools.historical_merge")
        if hasattr(hm, "merge_season"):
            hm.merge_season(season)
        else:
            print("⚠️ tools.historical_merge.merge_season not found; skipping append.")
    except Exception as e:
        print(f"⚠️ Could not run historical_merge: {e}")

def validate_inputs(season: int, week: int):
    now = datetime.now()
    if season < 2000 or season > now.year:
        raise ValueError(f"Season must be between 2000 and {now.year}.")
    if week < 1 or week > 18:
        raise ValueError("Week must be between 1 and 18.")

def main():
    parser = argparse.ArgumentParser(description="Run the working weekly_master build with season/week inputs.")
    parser.add_argument("--season", type=int, help="Season year, e.g. 2025")
    parser.add_argument("--week", type=int, help="Week number 1-18")
    parser.add_argument("--append", action="store_true", help="After build, refresh season master via historical_merge")
    args = parser.parse_args()

    if not args.season:
        args.season = int(input("Enter season year (e.g., 2025): ").strip())
    if not args.week:
        args.week = int(input("Enter week number (1-18): ").strip())

    try:
        validate_inputs(args.season, args.week)
    except ValueError as e:
        print(f"❌ Input error: {e}")
        sys.exit(1)

    mod = resolve_weekly_master()
    print(f"\n🚀 Delegating to weekly_master for season={args.season}, week={args.week}...\n")
    call_builder(mod, args.season, args.week)
    print("\n✅ weekly_master completed.\n")

    if args.append:
        print("🔄 Updating season master (historical_merge)...")
        historical_append(args.season)
        print("✅ Season master updated.")

if __name__ == "__main__":
    main()
