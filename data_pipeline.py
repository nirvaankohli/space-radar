#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path
import time

ROOT_DIR = Path(__file__).parent
LLM_SCRIPT = ROOT_DIR / "agents" / "llm" / "build.py"
CLEAN_SCRIPT = ROOT_DIR / "agents" / "cluster" / "clean.py"
BUILD_SCRIPT = ROOT_DIR / "agents" / "cluster" / "build.py"
DB_DIR = ROOT_DIR / "data" / "db"
stories_file = DB_DIR / "stories.json"


def run_script(script_path, description):
    print(f"\n=== {description} ===")
    start = time.time()

    try:
        # Use the virtual environment Python executable
        venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_executable = str(venv_python)
        else:
            python_executable = sys.executable
        print(python_executable, script_path)
        result = subprocess.run(
            [python_executable, str(script_path)],
            cwd=ROOT_DIR,
            timeout=3000,  # 5 minute timeout
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

    except subprocess.TimeoutExpired:
        print(f"✗ {description} timed out after 5 minutes")
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

    if stories_file.exists():
        print(f"✓ Final stories file exists: {stories_file}")
    else:
        print(f"✗ Missing final stories file: {stories_file}")


def run_pipeline():

    if not run_script(CLEAN_SCRIPT, "Article Cleaning & DB Update"):
        print("Pipeline failed at cleaning step")
        return 1
    if not run_script(BUILD_SCRIPT, "Story Clustering & Building"):
        print("Pipeline failed at building step")
        return 1
    if not run_script(LLM_SCRIPT, "LLM Processing"):
        print("Pipeline failed at LLM processing step")
        return 1

    return 0


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

    print(LLM_SCRIPT)

    if not run_script(LLM_SCRIPT, "LLM Processing"):
        print("Pipeline failed at LLM processing step")
        return 1

    print("\n=== Pipeline Completed Successfully ===")

    check_outputs()

    overall_elapsed = time.time() - overall_start
    print(f"\n Pipeline completed in {overall_elapsed:.2f} seconds")

    return 0


if __name__ == "__main__":
    main()
