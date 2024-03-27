import enum


class KlineColumns(enum.Enum):
    """Alternative column names."""

    KLINE_OPEN_TIME = 1
    OPEN_PRICE = 2
    HIGH_PRICE = 3
    LOW_PRICE = 4
    CLOSE_PRICE = 5
    VOLUME = 6
    KLINE_CLOSE_TIME = 7
    QUOTE_ASSET_VOLUME = 8
    NUMBER_OF_TRADES = 9
    TAKER_BUY_BASE_ASSET_VOLUME = 10
    TAKER_BUY_QUOTE_ASSET_VOLUME = 11

    @staticmethod
    def get_keys() -> list:
        """Get all keys of its."""
        return list(KlineColumns)


class STATUS(enum.Enum):
    """Alternative status."""

    TRADING = "TRADING"
    BREAK = "BREAK"
