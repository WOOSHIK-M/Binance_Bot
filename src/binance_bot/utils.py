import asyncio
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any


def call_limit(max_calls):
    """Limit the number of calls simultaneously."""
    semaphore = asyncio.Semaphore(max_calls)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with semaphore:
                f = await func(*args, **kwargs)
                await asyncio.sleep(1)
                return f

        return wrapper

    return decorator


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to timestamp."""
    return int(dt.timestamp() * 1000)


def save_pickle(obj: Any, fpath: str | Path) -> None:
    """Save object as pickle."""
    with open(fpath, "wb") as f:
        pickle.dump(obj, f)


def load_pickle(fpath: str | Path) -> object:
    """Load pickle file."""
    with open(fpath, "rb") as f:
        return pickle.load(f)
