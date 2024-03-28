import asyncio
import json
from datetime import datetime, timedelta, timezone

from annotations import KlineColumns
from client import Client


class TenbaggerScreener(Client):
    """Screen which coin is 10x."""

    async def is_tenbagger(self, symbol: str) -> bool:
        """Determine whether the coin is tenbagger.

        Tenbagger Condition:     The price has risen by over 10% in the last 3 hours.
        """
        print(symbol)
        data = await self.get_prices_timerange(
            symbol=symbol,
            interval="1m",
            limit=180,
        )

        # is tenbagger or not
        low_price = data[KlineColumns.LOW_PRICE].min()
        last_price = data[KlineColumns.CLOSE_PRICE][-1]
        increased_ratio = (last_price - low_price) / low_price

        if increased_ratio < 0.1:
            return None

        close_time = data[KlineColumns.KLINE_CLOSE_TIME][-1] // 1000
        kst_close_time = datetime.fromtimestamp(close_time, timezone(timedelta(hours=9)))
        return {
            "symbol": symbol,
            "kst_close_time": kst_close_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_price": last_price,
        }


async def detect_tenbagger() -> None:
    """Parse markets and their prices forever."""
    screener = TenbaggerScreener()
    while True:
        tasks = [
            asyncio.create_task(screener.is_tenbagger(symbol))
            for symbol in await screener.get_all_symbols()
        ]
        results = await asyncio.gather(*tasks)
        tenbaggers = [result for result in results if result is not None]

        msg = f" Current Time: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')} "
        if tenbaggers:
            print("#=" * ((len(msg) - 1) // 2 + 2) + "#")
            print(f"# {msg} #")
            print("#=" * ((len(msg) - 1) // 2 + 2) + "#")

            for idx, tenbagger in enumerate(tenbaggers):
                print(f"{idx} - {json.dumps(tenbagger)}")
            print()
        else:
            print(f"[{msg}] Any tenbagger is not detected.")
        await asyncio.sleep(60.0)


asyncio.run(detect_tenbagger())
