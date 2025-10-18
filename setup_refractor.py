"""
setup_refactor.py
------------------------------------
Automates structural cleanup and organization of the Fantasy V4 project.

✅ Creates __init__.py files for all src submodules
✅ Renames 'optomizer' → 'optimizer' and updates imports
✅ Moves loose scripts (like cleaner.py) to src/tools/
✅ Adds standardized data folders (processed, exports, logs)
✅ Generates src/utils/config_loader.py for YAML + logging config
✅ Creates a timestamped backup folder
✅ Writes a full change log with explanations to refactor_update_log.txt
✅ Supports --dry-run mode for previewing changes

Run:
    python setup_refactor.py
or
    python setup_refactor.py --dry-run
"""

import os
import re
import shutil
import datetime
import argparse
from pathlib import Path


# -------------------------------------------------------------
# 🧩 CONFIGURATION
# -------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
LOG_FILE = PROJECT_ROOT / "refactor_update_log.txt"

# Directories expected in /data
DATA_SUBDIRS = ["processed", "exports", "logs"]

# Files that should move to src/tools/
TOOLS_MOVE = ["cleaner.py", "run_framework_tests_fixed.py"]

# -------------------------------------------------------------
# 🛠️ HELPER FUNCTIONS
# -------------------------------------------------------------
def log_change(logs, action, target, reason):
    """Append a formatted change message to log list."""
    logs.append(f"[{action.upper()}] {target}\n    → Reason: {reason}\n")


def write_log(logs):
    """Write accumulated log entries to the log file."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        header = f"Refactor Update Log - {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f.write(header + "=" * 70 + "\n\n")
        f.writelines(logs)
        f.write("\nSummary:\n" + "-" * 70 + f"\nTotal Changes: {len(logs)}\n")
    print(f"\n📝 Refactor summary written to: {LOG_FILE}")


def make_backup():
    """Backup current project to timestamped folder."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_path = PROJECT_ROOT / f"backup_before_refactor_{timestamp}"
    if not backup_path.exists():
        shutil.copytree(PROJECT_ROOT, backup_path, dirs_exist_ok=True)
    return backup_path


def create_init_files(logs, dry_run=False):
    """Recursively create __init__.py files in src subdirectories."""
    for dirpath, dirnames, _ in os.walk(SRC_DIR):
        for dirname in dirnames:
            d = Path(dirpath) / dirname
            init_file = d / "__init__.py"
            if not init_file.exists():
                if not dry_run:
                    with open(init_file, "w", encoding="utf-8") as f:
                        f.write("# Makes this directory a Python package.\n")
                rel_path = str(init_file.relative_to(PROJECT_ROOT))
                log_change(logs, "ADDED", rel_path, "Ensures Python recognizes this folder as a module.")


def rename_optimizer(logs, dry_run=False):
    """Rename optomizer → optimizer and update imports."""
    old_path = SRC_DIR / "optomizer"
    new_path = SRC_DIR / "optimizer"

    if old_path.exists():
        if not dry_run:
            old_path.rename(new_path)
        log_change(logs, "RENAMED", f"{old_path} → {new_path}", "Fixes spelling to match standard imports.")

        # Update imports in all .py files
        for py_file in SRC_DIR.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            if "optomizer" in text:
                new_text = re.sub(r"optomizer", "optimizer", text)
                if not dry_run:
                    py_file.write_text(new_text, encoding="utf-8")
                log_change(logs, "UPDATED", str(py_file.relative_to(PROJECT_ROOT)),
                           "Adjusted imports referencing 'optomizer'.")


def move_tools(logs, dry_run=False):
    """Move loose utility scripts to src/tools/."""
    tools_dir = SRC_DIR / "tools"
    if not dry_run:
        tools_dir.mkdir(exist_ok=True)
    for filename in TOOLS_MOVE:
        old_path = PROJECT_ROOT / filename
        if old_path.exists():
            new_path = tools_dir / filename
            if not dry_run:
                shutil.move(str(old_path), str(new_path))
            log_change(logs, "MOVED", f"{old_path} → {new_path}", "Centralized loose utility scripts into src/tools/.")


def ensure_data_structure(logs, dry_run=False):
    """Ensure /data contains standard subdirectories."""
    for subdir in DATA_SUBDIRS:
        path = DATA_DIR / subdir
        if not path.exists():
            if not dry_run:
                path.mkdir(parents=True)
            log_change(logs, "ADDED", str(path.relative_to(PROJECT_ROOT)), "Creates consistent data subfolder structure.")


def create_config_loader(logs, dry_run=False):
    """Generate src/utils/config_loader.py if missing."""
    utils_dir = SRC_DIR / "utils"
    if not dry_run:
        utils_dir.mkdir(exist_ok=True)

    config_loader = utils_dir / "config_loader.py"
    if not config_loader.exists():
        content = '''"""
config_loader.py
------------------------------------
Centralizes YAML configuration and logging setup for Fantasy V4.
"""

import yaml
import logging
import logging.config
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

def load_settings():
    """Load general settings.yaml"""
    with open(CONFIG_DIR / "settings.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def setup_logging():
    """Configure logging from logging.yaml"""
    with open(CONFIG_DIR / "logging.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    logging.info("Logging configured successfully.")
'''
        if not dry_run:
            config_loader.write_text(content, encoding="utf-8")
        log_change(logs, "ADDED", str(config_loader.relative_to(PROJECT_ROOT)),
                   "Creates centralized YAML + logging configuration loader.")

# -------------------------------------------------------------
# 🚀 MAIN EXECUTION
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Automated project refactor tool.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files.")
    args = parser.parse_args()

    print("🛠️  Starting project refactor...")
    logs = []

    backup_path = make_backup()
    log_change(logs, "BACKUP", str(backup_path.relative_to(PROJECT_ROOT)), "Created pre-refactor backup of project.")

    create_init_files(logs, args.dry_run)
    rename_optimizer(logs, args.dry_run)
    move_tools(logs, args.dry_run)
    ensure_data_structure(logs, args.dry_run)
    create_config_loader(logs, args.dry_run)

    write_log(logs)
    print("\n✅ Refactor complete!" if not args.dry_run else "\n🔍 Dry-run complete (no files changed).")


if __name__ == "__main__":
    main()
