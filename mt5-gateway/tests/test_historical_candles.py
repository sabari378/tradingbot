from datetime import datetime, timezone

import pytest

from nirv_mt5.mt5_client import MT5Client


class FakeMT5:
    TIMEFRAME_M5 = 5

    def __init__(self) -> None:
        self.request = None
        self.shutdown_called = False

    def initialize(self, *, timeout: int) -> bool:
        assert timeout == 5000
        return True

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        self.request = (symbol, timeframe, date_from, date_to)
        return [
            {
                "time": 1_700_000_000,
                "open": 2000,
                "high": 2002,
                "low": 1999,
                "close": 2001,
                "tick_volume": 123,
                "spread": 15,
                "real_volume": 0,
            }
        ]

    def shutdown(self) -> None:
        self.shutdown_called = True


def test_historical_candles_uses_utc_and_preserves_mt5_fields() -> None:
    client = MT5Client()
    fake = FakeMT5()
    client.mt5 = fake

    candles = client.historical_candles(
        "XAUUSD",
        "M5",
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 1, 2, tzinfo=timezone.utc),
    )

    assert candles[0]["volume"] == 123.0
    assert candles[0]["spread"] == 15
    assert fake.request[0:2] == ("XAUUSD", 5)
    assert fake.request[2].tzinfo is timezone.utc
    assert fake.shutdown_called is True


def test_historical_candles_rejects_invalid_range_before_connecting() -> None:
    client = MT5Client()
    moment = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="earlier"):
        client.historical_candles("XAUUSD", "M5", moment, moment)
