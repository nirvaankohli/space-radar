from pathlib import Path
import yaml
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).parent.parent

possible_candidates = ["feeds.yml", "feeds.yaml", "feeds,yml"]
found: Optional[Path] = None

for name in possible_candidates:

    p = ROOT_DIR / name

    if p.exists():

        found = p
        break

if found is None:

    matches = list(ROOT_DIR.glob("feeds*"))
    found = matches[0] if matches else None

if found is None:

    raise FileNotFoundError(

        f"Feeds configuration file not found in {ROOT_DIR!s}. "
        f"Expected one of: {possible_candidates!s} or files matching 'feeds*'."
    
    )

FILE_PATH: Path = found


def load_feeds(file_path: Path = FILE_PATH) -> Dict[str, Any]:

    if not file_path or not file_path.exists():
        raise FileNotFoundError(f"Feeds configuration file not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    feeds_config = yaml.safe_load(text) or {}
    return feeds_config


if __name__ == "__main__":
    config = load_feeds()
    print(config)
