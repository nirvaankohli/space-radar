import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
LIB_DIR = ROOT_DIR / "data" / "agents"
LIB_NAME = "process_yml"


print(f"ROOT_DIR: {ROOT_DIR}")
print(f"LIB_DIR: {LIB_DIR}")
print(f"LIB_NAME: {LIB_NAME}")
print(f"ALL TOGETHER: {LIB_DIR / LIB_NAME}")
