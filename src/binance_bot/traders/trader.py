from abc import ABCMeta, abstractmethod

from binance_bot.common.annotations import ACTION, KlineColumns


class Trader(metaclass=ABCMeta):
    """A trader class."""

    TRADING_FEE = 0.001

    def __init__(self) -> None:
        """Initialize."""
        self.balance = 10000
        self.assets = 0

        self.keys = KlineColumns.get_keys()
        self.klines = {key: [] for key in self.keys}

    @abstractmethod
    def make_a_decision(self) -> ACTION:
        """Make a decision: buy, sell or do nothing."""
        pass

    def append_tick(self, tick_data: tuple[float]) -> None:
        """Save tick data to buffer."""
        for key, value in zip(self.keys, tick_data):
            self.klines[key].append(value)

    def _buy(self, ratio: float) -> None:
        """Buy assets."""
        money_to_spend = self.balance * ratio
        assets_to_buy = (money_to_spend * (1 - self.TRADING_FEE)) / self.estimated_price

        self.assets += assets_to_buy
        self.balance -= money_to_spend

    def _sell(self, ratio: float) -> None:
        """Sell assets."""
        assets_to_sell = self.assets * ratio

        self.assets -= assets_to_sell
        self.balance += self.estimated_price * assets_to_sell * (1 - self.TRADING_FEE)

    @property
    def estimated_price(self) -> float:
        """Estimate the current asset price."""
        return self.klines[KlineColumns.CLOSE_PRICE][-1]

    @property
    def estimated_balance(self) -> float:
        """Estimate all of my assets."""
        return self.balance + self.assets * self.estimated_price
