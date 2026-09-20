from nirv.strategies.chart_patterns import analyze_price_action


def candle(time: int, open_: float, high: float, low: float, close: float) -> dict:
    return {"time": time, "open": open_, "high": high, "low": low, "close": close, "volume": 100}


def test_price_action_labels_confirmed_swings_and_breaks() -> None:
    candles = [
        candle(1, 100, 102, 99, 101),
        candle(2, 101, 105, 100, 104),
        candle(3, 104, 104, 101, 102),
        candle(4, 102, 103, 98, 99),
        candle(5, 99, 102, 99, 101),
        candle(6, 101, 106, 100, 105.5),
        candle(7, 105, 107, 104, 106),
    ]

    result = analyze_price_action(candles, lookback=1)

    assert any(swing["kind"] == "HH" and swing["price"] == 105 for swing in result["swings"])
    assert any(item["direction"] == "bullish" for item in result["breaks"])


def test_price_action_returns_empty_annotations_for_flat_data() -> None:
    candles = [candle(index, 100, 101, 99, 100) for index in range(20)]
    result = analyze_price_action(candles)
    assert result["breaks"] == []
    assert result["patterns"] == []


def test_price_action_does_not_repeat_the_same_bos_on_consecutive_candles() -> None:
    candles = [
        candle(1, 100, 102, 99, 101),
        candle(2, 101, 105, 100, 104),
        candle(3, 104, 104, 101, 102),
        candle(4, 102, 103, 100, 101),
        candle(5, 101, 103, 100, 102),
        candle(6, 102, 107, 101, 106),
        candle(7, 106, 108, 105, 107),
    ]
    result = analyze_price_action(candles, lookback=1)
    assert len(result["breaks"]) == 1
