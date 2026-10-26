# Demo strategy monitor

Updated: 2026-09-15T17:08:27.502557-04:00

Balance: $9816.62; equity: $9822.42; broker positions: 7.

| Strategy | Entries | Open | Closed | Wins | Losses | Realized USD | Floating USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| sma_crossover | 1 | 1 | 0 | 0 | 0 | 0 | 7.99 |
| donchian_breakout | 2 | 1 | 1 | 0 | 1 | -13.51 | -9.79 |
| bollinger_reversion | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rsi_countertrend | 1 | 0 | 1 | 0 | 1 | -12.74 | 0 |
| volatility_breakout | 2 | 1 | 1 | 0 | 1 | -13.54 | -9.79 |
| engulfing_reversal | 5 | 1 | 3 | 0 | 3 | -56.44 | 7.73 |
| market_structure | 8 | 1 | 7 | 2 | 5 | -8.91 | -9.79 |
| liquidity_sweep | 2 | 0 | 2 | 1 | 1 | 23.5 | 0 |
| fair_value_gap | 4 | 2 | 2 | 0 | 2 | -43.37 | 19.45 |
| double_top | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Individual trades

| Ticket | Strategy | TF | Side | Lots | Status | Realized USD | Floating USD | Exit |
|---|---|---|---|---:|---|---:|---:|---|
| 1024939899 | sma_crossover | M15 | BUY | 0.01 | OPEN | 0.0 | 7.99 |  |
| 1024601325 | donchian_breakout | M15 | BUY | 0.01 | CLOSED | -13.51 | 0 | SL |
| 1025078679 | donchian_breakout | M15 | BUY | 0.01 | OPEN | 0.0 | -9.79 |  |
| 1024771382 | rsi_countertrend | M15 | SELL | 0.01 | CLOSED | -12.74 | 0 | SL |
| 1024601329 | volatility_breakout | M15 | BUY | 0.01 | CLOSED | -13.54 | 0 | SL |
| 1025078680 | volatility_breakout | M15 | BUY | 0.01 | OPEN | 0.0 | -9.79 |  |
| 1024771384 | engulfing_reversal | M30 | SELL | 0.01 | CLOSED | -18.72 | 0 | SL |
| 1024837503 | engulfing_reversal | H1 | SELL | 0.01 | CLOSED | -22.69 | 0 | SL |
| 1024861701 | engulfing_reversal | M15 | BUY | 0.01 | OPEN | 0.0 | 7.73 |  |
| 1024939903 | engulfing_reversal | M15 | SELL | 0.01 | CLOSED | -15.03 | 0 | SL |
| 1024994686 | engulfing_reversal | M15 | SELL | 0.01 | UNRESOLVED | 0.0 | None |  |
| 1024477591 | market_structure | M15 | BUY | 0.02 | CLOSED | -22.84 | 0 | SL |
| 1024477594 | market_structure | H1 | SELL | 0.01 | CLOSED | -18.62 | 0 | SL |
| 1024487469 | market_structure | M15 | BUY | 0.02 | CLOSED | -18.0 | 0 | SL |
| 1024508132 | market_structure | M15 | BUY | 0.02 | CLOSED | 40.6 | 0 | TP |
| 1024531066 | market_structure | M15 | BUY | 0.02 | CLOSED | 37.46 | 0 | TP |
| 1024601341 | market_structure | M15 | BUY | 0.01 | CLOSED | -13.68 | 0 | SL |
| 1024647974 | market_structure | M15 | BUY | 0.01 | CLOSED | -13.83 | 0 | SL |
| 1025078684 | market_structure | M15 | BUY | 0.01 | OPEN | 0.0 | -9.79 |  |
| 1024707369 | liquidity_sweep | M15 | SELL | 0.04 | CLOSED | -20.6 | 0 | SL |
| 1024735750 | liquidity_sweep | M15 | SELL | 0.03 | CLOSED | 44.1 | 0 | TP |
| 1024477592 | fair_value_gap | M30 | BUY | 0.01 | OPEN | 0.0 | 9.73 |  |
| 1024487470 | fair_value_gap | H1 | BUY | 0.01 | OPEN | 0.0 | 9.72 |  |
| 1024531069 | fair_value_gap | M15 | SELL | 0.02 | CLOSED | -20.52 | 0 | SL |
| 1024808599 | fair_value_gap | M15 | SELL | 0.01 | CLOSED | -22.85 | 0 | SL |

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
