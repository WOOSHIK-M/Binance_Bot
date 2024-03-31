import numpy as np
import pandas as pd

from binance_bot.common.annotations import ACTION, KlineColumns
from binance_bot.traders.trader import Trader


class MovingAverageTrader(Trader):
    """."""

    def make_a_decision(self) -> ACTION:
        """."""
        prices = self.klines[KlineColumns.CLOSE_PRICE]

        short_mavg = self._compute_moving_average(prices, window=10)
        long_mavg = self._compute_moving_average(prices, window=50)

        signals = np.array(short_mavg > long_mavg)
        crossed = (signals != np.roll(signals, 1))[-1]

        if not crossed:
            return ACTION.DO_NOTHING

        if signals[-1]:
            self._buy(ratio=0.5)
            return ACTION.BUY

        self._sell(ratio=0.2)
        return ACTION.SELL

    def _compute_moving_average(self, prices: np.ndarray, window: int) -> np.ndarray:
        """."""
        prices = pd.Series(prices)
        return prices.rolling(window=window, min_periods=1).mean()
