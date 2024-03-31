import random

from binance_bot.common.annotations import ACTION
from binance_bot.traders.trader import Trader


class RandomActionTrader(Trader):
    """A trader class with random actions."""

    def make_a_decision(self) -> ACTION:
        """Make a decision randomly."""
        prob = random.random()
        if prob < 1 / 6:
            self._buy(ratio=random.random())
            return ACTION.BUY
        elif 1 / 6 <= prob < 2 / 6:
            self._sell(ratio=random.random())
            return ACTION.SELL
        else:
            return ACTION.DO_NOTHING
