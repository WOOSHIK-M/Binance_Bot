import asyncio
from datetime import datetime, timedelta, timezone

import aiohttp
import numpy as np

import binance_bot.common.utils as utils
from binance_bot.common.annotations import STATUS, KlineColumns


class Client:
    """A base binance client."""

    API_URL = "https://api.binance.com/api/v3"

    def __init__(self) -> None:
        """Initialize."""
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50))

    async def get_all_symbols(self) -> list[str]:
        """Get all symbols from binance.

        Notes:
            - It is implemented at every 6 hours.
            - It only takes usdt-based symbols.

        response = {
            "symbol": "LTCBTC",
            "price": "4.00000200"
        }

        Reference:
            https://binance-docs.github.io/apidocs/spot/en/#exchange-information
        """
        data = await self._request(url=f"{self.API_URL}/exchangeInfo")

        # only get spots with trading status
        data = [
            info["symbol"]
            for info in data["symbols"]
            if (info["quoteAsset"] == "USDT" and info["status"] == STATUS.TRADING.value)
        ]
        return data[:1]

    async def get_prices_in_period(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, np.ndarray]:
        """Get previous candles with the given time range."""
        tasks = []
        while True:
            tasks.append(
                self.get_prices_of_(symbol=symbol, start_time=start_time, end_time=end_time)
            )
            start_time += timedelta(minutes=1000)
            if start_time >= end_time - timedelta(seconds=1):
                break

        results = await asyncio.gather(*tasks)

        # merge the results
        data = {}
        for key, value in results[0].items():
            for tmp_data in results[1:]:
                value = np.concatenate([value, tmp_data[key]])
            data[key] = value
        return data

    async def get_prices_of_(
        self,
        symbol: str,
        interval: str = "1m",
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000,
    ) -> dict[str, np.ndarray]:
        """Get previous candles.

        Reference:
            https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

        Arguments:
            symbol: a market symbol to request data.
            interval: time interval of ticks.
            start_time: if it is not given, parse the recent 100 days.
            end_time: if it is not given, parse data until today.
            limit: the number of ticks to receive.

        response = [
            [
                1499040000000,      // Kline open time
                "0.01634790",       // Open price
                "0.80000000",       // High price
                "0.01575800",       // Low price
                "0.01577100",       // Close price
                "148976.11427815",  // Volume
                1499644799999,      // Kline Close time
                "2434.19055334",    // Quote asset volume
                308,                // Number of trades
                "1756.87402397",    // Taker buy base asset volume
                "28.46694368",      // Taker buy quote asset volume
                "0"                 // Unused field, ignore.
            ]
        ]
        """
        assert interval == "1m", "Other intervals are not supported."

        end_time = end_time or datetime.now(timezone.utc)
        start_time = start_time or end_time - timedelta(minutes=limit)

        data = await self._request(
            url=f"{self.API_URL}/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "startTime": utils.datetime_to_timestamp(start_time),
                "endTime": utils.datetime_to_timestamp(end_time),
            },
        )
        data = np.array(data).astype(np.float_)
        data = dict(zip(KlineColumns.get_keys(), data.transpose()))
        return data

    @utils.rate_limiter(max_calls=50)
    async def _request(
        self,
        url: str,
        params: dict = None,
        timeout: int = 10,
    ) -> object:
        """Request data.

        Notes:
            - It is recommended calling this by parallel in a single process!
            - It is limited to call 6000 times in a miniute.
        """
        async with self.session.get(url=url, params=params, timeout=timeout) as response:
            return await response.json()

    def __del__(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.session.close())
