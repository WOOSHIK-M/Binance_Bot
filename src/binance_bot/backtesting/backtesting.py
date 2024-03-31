import asyncio
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from tqdm import tqdm

import binance_bot.common.utils as utils
from binance_bot.common.annotations import ACTION, KlineColumns
from binance_bot.common.client import Client
from binance_bot.traders import MovingAverageTrader as Trader


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
        n_data = 1000
        idx = random.randint(a=0, b=len(data[KlineColumns.OPEN_PRICE]) - n_data)
        for key, value in data.items():
            data[key] = value[idx : idx + n_data]

        # do trading
        trader = Trader()

        balances, decisions = [], []
        for tick_data in zip(*data.values()):
            trader.append_tick(tick_data)
            decision = trader.make_a_decision()

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
while True:
    asyncio.run(do_backtesting())
    time.sleep(1)
