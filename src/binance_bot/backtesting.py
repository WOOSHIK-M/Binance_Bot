import asyncio
import enum
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import utils
from client import Client
from config import KlineColumns
from plotly.subplots import make_subplots
from tqdm import tqdm


class ACTION(enum.Enum):
    """Action class."""

    BUY = 1
    DO_NOTHING = 0
    SELL = -1


class Trader:
    """A trader class."""

    TRADING_FEE = 0.1

    def __init__(self) -> None:
        """Initialize."""
        self.balance = 10000
        self.assets = 0

        self.keys = KlineColumns.get_keys()
        self.klines = {key: [] for key in self.keys}

    def make_a_decision(self, tick_data) -> int:
        """."""
        # store a tick data
        for key, value in zip(self.keys, tick_data):
            self.klines[key].append(value)

        return self.do_a_random_action()

    def do_a_random_action(self) -> ACTION:
        """Buy, sell or do nothing randomly."""
        prob = random.random()
        if prob < 1 / 6:
            self._buy(ratio=random.random())
            return ACTION.BUY
        elif 1 / 6 <= prob < 2 / 6:
            self._sell(ratio=random.random())
            return ACTION.SELL
        else:
            return ACTION.DO_NOTHING

    def _buy(self, ratio: float) -> None:
        """."""
        money_to_spend = self.balance * ratio
        assets_to_buy = (money_to_spend * (1 - self.TRADING_FEE)) / self.estimated_price

        self.assets += assets_to_buy
        self.balance -= money_to_spend

    def _sell(self, ratio: float) -> None:
        """."""
        assets_to_sell = self.assets * ratio

        self.assets -= assets_to_sell
        self.balance += self.estimated_balance * assets_to_sell * (1 - self.TRADING_FEE)

    @property
    def estimated_price(self) -> float:
        """."""
        return self.klines[KlineColumns.CLOSE_PRICE][-1]

    @property
    def estimated_balance(self) -> float:
        """."""
        return self.balance + self.assets * self.estimated_price


class Backtester(Client):
    """A class to back-testing."""

    DIR_NAME = "data"
    FILE_NAME = "data.pkl"
    IMG_NAME = "image.png"

    def __init__(self, **kwargs) -> None:
        """Initialize."""
        super().__init__(**kwargs)

        self.save_dir = Path(self.DIR_NAME)
        self.save_dir.mkdir(exist_ok=True)

    async def do_backtesting(self, symbol: str) -> None:
        """Do backtesting."""
        data = utils.load_pickle(fpath=self.save_dir / symbol / self.FILE_NAME)

        # use partial of them
        for key, value in data.items():
            data[key] = value[-500:]

        # do trading
        trader = Trader()

        balances, decisions = [], []
        for tick_data in zip(*data.values()):
            decision = trader.make_a_decision(tick_data)

            decisions.append(decision)
            balances.append(trader.estimated_balance)

        self.plot_candle_chart(
            symbol=symbol,
            data=data,
            balances=balances,
            decisions=decisions,
        )

    def plot_candle_chart(
        self,
        symbol: str,
        data: dict[KlineColumns, np.ndarray],
        balances: list[float] = None,
        decisions: list[int] = None,
    ) -> None:
        """."""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("OHCL", "Volumne"),
            row_width=[0.3, 0.7],
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
        )

        times = [datetime.fromtimestamp(ts // 1000) for ts in data[KlineColumns.KLINE_OPEN_TIME]]

        # ohlc
        fig.add_trace(
            go.Candlestick(
                x=times,
                open=data[KlineColumns.OPEN_PRICE],
                close=data[KlineColumns.CLOSE_PRICE],
                high=data[KlineColumns.HIGH_PRICE],
                low=data[KlineColumns.LOW_PRICE],
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        if balances:
            # balance changes
            fig.add_trace(
                go.Scatter(x=times, y=balances, showlegend=False),
                secondary_y=True,
                row=1,
                col=1,
            )

            # buy flag
            buy = [
                (times[idx], data[KlineColumns.HIGH_PRICE][idx])
                for idx, decision in enumerate(decisions)
                if decision == ACTION.BUY
            ]
            xs, ys = np.array(buy).transpose()
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    marker=dict(
                        size=12,
                        line=dict(
                            width=2,
                            color="DarkSlateGrey",
                        ),
                    ),
                    marker_symbol="triangle-down",
                    text=["BUY"] * len(xs),
                    textposition="top center",
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

            # sell flag
            sell = [
                (times[idx], data[KlineColumns.LOW_PRICE][idx])
                for idx, decision in enumerate(decisions)
                if decision == ACTION.SELL
            ]
            xs, ys = np.array(sell).transpose()
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    marker=dict(
                        size=12,
                        line=dict(
                            width=2,
                            color="DarkSlateGrey",
                        ),
                    ),
                    marker_symbol="triangle-up",
                    text=["SELL"] * len(xs),
                    textposition="top center",
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

        # volumne
        fig.add_trace(
            go.Bar(x=times, y=data[KlineColumns.VOLUME], showlegend=False),
            row=2,
            col=1,
        )

        fig.update_layout(
            title=symbol,
            xaxis_rangeslider_visible=False,
            width=6000,
            height=1800,
        )
        pio.write_image(fig, self.save_dir / symbol / self.IMG_NAME)

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
    """Get candle data of all markets."""
    worker = Backtester()

    pbar = tqdm(await worker.get_all_symbols())
    for symbol in pbar:
        pbar.set_description(f"Loading {symbol}")
        await worker.dump(symbol)


async def do_backtesting() -> None:
    """Do backtesting."""
    worker = Backtester()
    # pbar = tqdm(await worker.get_all_symbols())
    # for symbol in pbar:
    #     pbar.set_description(f"Testing {symbol}")
    #     await worker.dump(symbol)

    await worker.do_backtesting(symbol="BTCUSDT")


# asyncio.run(dump_all_candles())
asyncio.run(do_backtesting())
