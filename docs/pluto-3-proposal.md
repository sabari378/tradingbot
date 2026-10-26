# Pluto 3 - proposed test

Status: proposal only; not started.

Review covers all 163 broker-reconciled Pluto trades, including the eight excluded from the frozen original baseline. The frozen baseline remains unchanged.

| Strategy | Closed trades | Net USD |
|---|---:|---:|
| bollinger_reversion | 9 | 74.66 |
| donchian_breakout | 22 | 32.60 |
| engulfing_reversal | 15 | 15.34 |
| fair_value_gap | 9 | 1.41 |
| liquidity_sweep | 22 | -42.82 |
| market_structure | 62 | -139.79 |
| rsi_countertrend | 9 | 144.74 |
| sma_crossover | 4 | 27.12 |
| volatility_breakout | 11 | 0.92 |
| double_top | 0 | 0.00 |

Proposed single change: require a fresh crossing of the currently confirmed swing level for Market Structure entries, rather than permitting an entry on every subsequent close beyond that level. Evaluate both the previous and current close against the same level, using only swings confirmed before the signal candle. Keep all other strategy rules, timeframes, SL/TP and sizing unchanged.

Hypothesis: reduce repeated exposure to the same structural move. This review does not prove it will improve results. Validate prospectively and log the swing level and previous/current close for each decision.

No orders or strategy settings were changed during this review.


## Applied September 17, 2026

Approved fresh-cross rule implemented only for Market Structure. All 81 backend tests passed. Pluto 3 started at 07:19 Indianapolis time and stops new entries at 17:00 today. Existing broker SL/TP remain after cutoff. Session: `backend/data/pluto3-20260917-071903`. All ten strategies scanned M15, M30 and H1; the first fill was Liquidity Sweep.
