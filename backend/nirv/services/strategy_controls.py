import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from nirv.core.config import get_settings
from nirv.strategies.catalog import CATALOG_STRATEGIES

_lock = Lock()


def controls_path() -> Path:
    return Path(get_settings().data_dir) / 'strategy-controls.json'


def enabled_strategies() -> dict[str, bool]:
    path = controls_path()
    if not path.exists():
        return dict.fromkeys(CATALOG_STRATEGIES, True)
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or any(type(v) is not bool for v in data.values()):
        raise ValueError('invalid strategy controls')
    return {s: data.get(s, True) for s in CATALOG_STRATEGIES}


def strategy_enabled(strategy: str) -> bool:
    try:
        return enabled_strategies().get(strategy, False)
    except (ValueError, OSError):
        return False


def set_strategy_enabled(strategy: str, enabled: bool) -> dict[str, bool]:
    if strategy not in CATALOG_STRATEGIES:
        raise ValueError('unknown strategy')
    with _lock:
        data = enabled_strategies()
        data[strategy] = enabled
        path = controls_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f'{path.name}.{uuid4().hex}.tmp')
        temp.write_text(json.dumps(data))
        os.replace(temp, path)
        return data
