from pathlib import Path
from typing import Any, Dict, List
import yaml

CONCEPTS_DIR = Path(__file__).parent


def load_raw_conceptcards() -> List[Dict[str, Any]]:
    conceptcards: List[Dict[str, Any]] = []

    for path in sorted(CONCEPTS_DIR.glob("*.yaml")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML in {path.name}") from e
        except OSError as e:
            raise ValueError(f"Failed to read file {path.name}") from e

        if data is None:
            raise ValueError(f"{path.name} is empty or invalid YAML")

        if not isinstance(data, dict):
            raise ValueError(f"{path.name} must contain a YAML mapping at the top level")

        conceptcards.append(data)

    return conceptcards

