import json
from pathlib import Path

UPDATE_HISTORY_FILE = Path("data/update_history.json")


def load_update_history() -> list[dict]:
    try:
        if not UPDATE_HISTORY_FILE.exists():
            return []
        with UPDATE_HISTORY_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_update_history(entries: list[dict]) -> None:
    UPDATE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with UPDATE_HISTORY_FILE.open("w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)


def append_update(entry: dict) -> None:
    items = load_update_history()
    items.insert(0, entry)
    save_update_history(items)
