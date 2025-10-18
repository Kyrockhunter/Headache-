"""
check_csv_usage.py
----------------------------------------
Scans the entire Fantasy V4 project for CSV file usage.

✅ Finds all .csv files physically present in the repo
✅ Finds all .csv filenames referenced in Python source files
✅ Compares both lists and reports:
    - ✅ CSVs referenced in code
    - ❌ CSVs not referenced (safe to delete or archive)
✅ Logs results to data/logs/csv_usage_report.txt
"""

import os
import re
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # root of project
DATA_DIR = PROJECT_ROOT / "data"
LOG_FILE = DATA_DIR / "logs" / "csv_usage_report.txt"

SEARCH_EXTS = [".py"]
CSV_EXT = ".csv"

# --- UTILITIES ---
def find_all_csv_files():
    """Return a list of all CSV files under the project root."""
    csv_files = []
    for path in PROJECT_ROOT.rglob(f"*{CSV_EXT}"):
        if ".venv" not in str(path) and "backup_before_refactor" not in str(path):
            csv_files.append(path.relative_to(PROJECT_ROOT))
    return csv_files


def find_csv_references():
    """Scan all .py files for references to .csv filenames."""
    csv_pattern = re.compile(r'[\w\-/\\]+\.csv', re.IGNORECASE)
    references = set()

    for py_file in PROJECT_ROOT.rglob("*.py"):
        if ".venv" in str(py_file) or "backup_before_refactor" in str(py_file):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
            for match in csv_pattern.findall(text):
                if not match.lower().startswith("http"):  # skip URLs
                    references.add(Path(match).name)
        except Exception as e:
            print(f"⚠️ Skipped {py_file}: {e}")
    return references


def compare_csv_usage():
    """Compare found CSVs vs those referenced in code."""
    all_csvs = find_all_csv_files()
    referenced = find_csv_references()

    used = []
    unused = []

    for csv_file in all_csvs:
        if csv_file.name in referenced:
            used.append(csv_file)
        else:
            unused.append(csv_file)

    return used, unused


def write_report(used, unused):
    """Write results to log file and print summary."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        header = f"CSV Usage Report - {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f.write(header + "=" * 70 + "\n\n")

        f.write("✅ USED CSV FILES (referenced in code)\n" + "-" * 70 + "\n")
        if used:
            for u in used:
                f.write(f"{u}\n")
        else:
            f.write("None found.\n")

        f.write("\n❌ UNUSED CSV FILES (not referenced in any Python file)\n" + "-" * 70 + "\n")
        if unused:
            for u in unused:
                f.write(f"{u}\n")
        else:
            f.write("None found.\n")

    print(f"\n📝 CSV usage report saved to: {LOG_FILE}")
    print(f"✅ {len(used)} used | ❌ {len(unused)} unused")


def main():
    print("🔍 Scanning project for CSV file usage...")
    used, unused = compare_csv_usage()
    write_report(used, unused)


if __name__ == "__main__":
    main()
