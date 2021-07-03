from pathlib import Path
import pickle
from typing import Any


def load_pickle(path: Path) -> Any:
    with open(path, "rb") as f:
        content = pickle.load(f)
    return content


def dump_pickle(path: Path, content: Any) -> None:
    with open(path, "wb") as f:
        pickle.dump(content, f)
