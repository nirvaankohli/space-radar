#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
import time

ROOT_DIR = Path(__file__).parent
CLEAN_SCRIPT = ROOT_DIR / "agents" / "cluster" / "clean.py"
BUILD_SCRIPT = ROOT_DIR / "agents" / "cluster" / "build.py"
DB_DIR = ROOT_DIR / "data" / "db"
FINAL_OUTPUT = ROOT_DIR / "stories.json"


def run_script(script_path, description):
    print(f"\n=== {description} ===")
    start = time.time()

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )

        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"✗ {description} failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"✗ Error running {description}: {e}")
        return False

    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f} seconds")
    return True


def check_outputs():
    print("\n=== Checking Pipeline Outputs ===")

    index_file = DB_DIR / "index.json"
    by_date_dir = DB_DIR / "by_date"
    story_candidates_file = DB_DIR / "story_candidates.json"

    if index_file.exists():
        print(f"✓ Index file exists: {index_file}")
        try:
            import json

            with open(index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = "id" if "id" in data else "ids"
                count = len(data.get(key, []))
                print(f"  - Contains {count} article IDs")
        except Exception as e:
            print(f"  - Error reading index: {e}")
    else:
        print(f"✗ Missing index file: {index_file}")

    if by_date_dir.exists():
        date_files = list(by_date_dir.glob("*.json"))
        print(f"✓ By-date directory exists with {len(date_files)} files")
        for file in sorted(date_files)[-3:]:  # Show last 3 files
            try:
                import json

                with open(file, "r", encoding="utf-8") as f:
                    articles = json.load(f)
                    print(f"  - {file.name}: {len(articles)} articles")
            except Exception as e:
                print(f"  - {file.name}: Error reading ({e})")
    else:
        print(f"✗ Missing by-date directory: {by_date_dir}")

    if story_candidates_file.exists():
        print(f"✓ Story candidates file exists: {story_candidates_file}")
        try:
            import json

            with open(story_candidates_file, "r", encoding="utf-8") as f:
                stories = json.load(f)
                print(f"  - Contains {len(stories)} story candidates")

                # Copy to final output location
                import shutil

                shutil.copy2(story_candidates_file, FINAL_OUTPUT)
                print(f"✓ Copied to final output: {FINAL_OUTPUT}")

        except Exception as e:
            print(f"  - Error processing story candidates: {e}")
    else:
        print(f"✗ Missing story candidates file: {story_candidates_file}")


def main():
    print(" Space Radar Data Pipeline")
    print(f"Working directory: {ROOT_DIR}")

    overall_start = time.time()

    # Step 1: Clean and process articles
    if not run_script(CLEAN_SCRIPT, "Article Cleaning & DB Update"):
        print("Pipeline failed at cleaning step")
        return 1

    # Step 2: Build story candidates from clusters
    if not run_script(BUILD_SCRIPT, "Story Clustering & Building"):
        print("Pipeline failed at building step")
        return 1

    # Step 3: Check all outputs
    check_outputs()

    overall_elapsed = time.time() - overall_start
    print(f"\n Pipeline completed in {overall_elapsed:.2f} seconds")
    print(f" Final output available at: {FINAL_OUTPUT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
