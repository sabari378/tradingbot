# Demo strategy monitor

Updated: 2026-09-16T17:22:52.708995-04:00

Balance: $10024.11; equity: $10033.80; broker positions: 4.

| Strategy | Entries | Open | Closed | Wins | Losses | Realized USD | Floating USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| sma_crossover | 1 | 1 | 0 | 0 | 0 | 0 | 2.44 |
| donchian_breakout | 3 | 1 | 2 | 2 | 0 | 77.63 | 2.51 |
| bollinger_reversion | 1 | 0 | 1 | 0 | 1 | -22.27 | 0 |
| rsi_countertrend | 1 | 0 | 1 | 1 | 0 | 47.34 | 0 |
| volatility_breakout | 3 | 1 | 2 | 2 | 0 | 80.07 | 2.51 |
| engulfing_reversal | 2 | 0 | 2 | 0 | 2 | -29.83 | 0 |
| market_structure | 5 | 1 | 4 | 3 | 1 | 95.09 | 2.23 |
| liquidity_sweep | 7 | 0 | 7 | 0 | 7 | -160.12 | 0 |
| fair_value_gap | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| double_top | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Individual trades

| Ticket | Strategy | TF | Side | Lots | Status | Realized USD | Floating USD | Exit |
|---|---|---|---|---:|---|---:|---:|---|
| 1026922910 | sma_crossover | M15 | SELL | 0.01 | OPEN | 0.0 | 2.44 |  |
| 1026669401 | donchian_breakout | M15 | SELL | 0.01 | CLOSED | 32.1 | 0 | TP |
| 1026854466 | donchian_breakout | M15 | SELL | 0.01 | CLOSED | 45.53 | 0 | TP |
| 1026922924 | donchian_breakout | M15 | SELL | 0.01 | OPEN | 0.0 | 2.51 |  |
| 1026669417 | bollinger_reversion | M15 | BUY | 0.01 | CLOSED | -22.27 | 0 | SL |
| 1026409457 | rsi_countertrend | H1 | SELL | 0.01 | CLOSED | 47.34 | 0 | TP |
| 1026669430 | volatility_breakout | M15 | SELL | 0.01 | CLOSED | 31.95 | 0 | TP |
| 1026854477 | volatility_breakout | M15 | SELL | 0.01 | CLOSED | 48.12 | 0 | TP |
| 1026922932 | volatility_breakout | M15 | SELL | 0.01 | OPEN | 0.0 | 2.51 |  |
| 1026370628 | engulfing_reversal | M15 | SELL | 0.01 | CLOSED | -15.58 | 0 | SL |
| 1026441966 | engulfing_reversal | M15 | BUY | 0.01 | CLOSED | -14.25 | 0 | SL |
| 1026409462 | market_structure | H1 | BUY | 0.01 | CLOSED | -22.7 | 0 | SL |
| 1026669438 | market_structure | M15 | SELL | 0.01 | CLOSED | 30.95 | 0 | TP |
| 1026735615 | market_structure | M15 | SELL | 0.01 | CLOSED | 41.24 | 0 | TP |
| 1026854492 | market_structure | M15 | SELL | 0.01 | CLOSED | 45.6 | 0 | TP |
| 1026922938 | market_structure | M15 | SELL | 0.01 | OPEN | 0.0 | 2.23 |  |
| 1026353712 | liquidity_sweep | M15 | SELL | 0.02 | CLOSED | -26.18 | 0 | SL |
| 1026353714 | liquidity_sweep | M30 | SELL | 0.02 | CLOSED | -26.18 | 0 | SL |
| 1026353716 | liquidity_sweep | H1 | SELL | 0.02 | CLOSED | -26.18 | 0 | SL |
| 1026521309 | liquidity_sweep | M15 | SELL | 0.04 | CLOSED | -23.16 | 0 | SL |
| 1026521387 | liquidity_sweep | M30 | SELL | 0.04 | CLOSED | -26.04 | 0 | SL |
| 1026521484 | liquidity_sweep | H1 | SELL | 0.04 | CLOSED | -15.52 | 0 | SL |
| 1026735621 | liquidity_sweep | M15 | BUY | 0.01 | CLOSED | -16.86 | 0 | SL |

## Entry rules

- **sma_crossover:** Fresh 20/50 SMA crossover
- **donchian_breakout:** Close beyond the previous 20-candle range
- **bollinger_reversion:** Fresh close outside the 2-standard-deviation band; countertrend entry
- **rsi_countertrend:** RSI crosses back above 30 or below 70
- **volatility_breakout:** 20-candle breakout with range at least 1.5 ATR
- **engulfing_reversal:** Current body engulfs the previous opposite-direction body
- **market_structure:** Close beyond the latest confirmed swing; fresh crossing is not required
- **liquidity_sweep:** Sweep of the previous 20-candle extreme followed by a close back inside
- **fair_value_gap:** New three-candle imbalance
- **double_top:** Two similar swing highs, bearish displacement and previous-low break

Each strategy/timeframe can enter once per qualifying candle, including while earlier positions remain open. Different strategies can respond to the same market move. Market Structure does not require a fresh crossing of the swing level.

Broker tickets are used for reconciliation because broker history timestamps may differ from local time. Unresolved history is not treated as a confirmed close.
