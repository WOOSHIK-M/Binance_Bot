import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import utils
from client import Client
from tqdm import tqdm


class Backtester(Client):
    """A class to back-testing."""

    DIR_NAME = "data"
    FILE_NAME = "data.pkl"

    def __init__(self, **kwargs) -> None:
        """Initialize."""
        super().__init__(**kwargs)

        self.save_dir = Path(self.DIR_NAME)
        self.save_dir.mkdir(exist_ok=True)

    async def dump(self, symbol: str) -> None:
        """Dump candle data of the given market."""
        data = await self.get_prices_in_period(
            symbol=symbol,
            start_time=datetime.now(timezone.utc) - timedelta(days=100),
            end_time=datetime.now(timezone.utc),
        )

        # save
        save_dir = self.save_dir / symbol
        save_dir.mkdir(exist_ok=True)

        utils.save_pickle(obj=data, fpath=save_dir / self.FILE_NAME)


async def dump_all_candles():
    """Run."""
    worker = Backtester()

    pbar = tqdm(await worker.get_all_symbols())
    for symbol in pbar:
        pbar.set_description(f"Loading {symbol}")
        await worker.dump(symbol)


asyncio.run(dump_all_candles())
