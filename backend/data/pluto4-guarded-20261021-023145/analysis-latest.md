# Demo strategy monitor

Updated: 2026-10-21T10:55:50.708424-04:00

Balance: $9958.92; equity: $9962.95; broker positions: 2.

| Strategy | Entries | Open | Closed | Wins | Losses | Realized USD | Floating USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| sma_crossover | 1 | 0 | 1 | 0 | 1 | -24.69 | 0 |
| donchian_breakout | 3 | 1 | 2 | 0 | 2 | -43.86 | -0.91 |
| bollinger_reversion | 2 | 0 | 2 | 2 | 0 | 72.8 | 0 |
| rsi_countertrend | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| volatility_breakout | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| engulfing_reversal | 1 | 1 | 0 | 0 | 0 | 0 | 4.94 |
| market_structure | 2 | 0 | 2 | 0 | 2 | -29.65 | 0 |
| liquidity_sweep | 1 | 0 | 1 | 1 | 0 | 30.08 | 0 |
| fair_value_gap | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| double_top | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Individual trades

| Ticket | Strategy | TF | Side | Lots | Status | Realized USD | Floating USD | Exit |
|---|---|---|---|---:|---|---:|---:|---|
| 1062661160 | sma_crossover | M15 | BUY | 0.03 | CLOSED | -24.69 | 0 | SL |
| 1062475603 | donchian_breakout | M15 | BUY | 0.02 | CLOSED | -22.52 | 0 | SL |
| 1062551197 | donchian_breakout | M15 | SELL | 0.02 | CLOSED | -21.34 | 0 | SL |
| 1062768149 | donchian_breakout | M30 | BUY | 0.01 | OPEN | 0.0 | -0.91 |  |
| 1062475615 | bollinger_reversion | M15 | SELL | 0.02 | CLOSED | 22.16 | 0 | TP |
| 1062794435 | bollinger_reversion | M15 | SELL | 0.03 | CLOSED | 50.64 | 0 | TP |
| 1062824942 | engulfing_reversal | M15 | SELL | 0.01 | OPEN | 0.0 | 4.94 |  |
| 1062372528 | market_structure | M30 | SELL | 0.02 | CLOSED | -21.4 | 0 | SL |
| 1062695436 | market_structure | M15 | SELL | 0.01 | CLOSED | -8.25 | 0 | SL |
| 1062372530 | liquidity_sweep | H1 | BUY | 0.02 | CLOSED | 30.08 | 0 | TP |

Pluto 4 additions: Liquidity Sweep requires a directional close in the outer third; Engulfing requires a test of the previous 20-bar extreme. Filtered baseline signals are logged in SCAN records.

## Entry rules

- **sma_crossover:** Fresh 20/50 SMA crossover
- **donchian_breakout:** Close beyond the previous 20-candle range
- **bollinger_reversion:** Fresh close outside the 2-standard-deviation band; countertrend entry
- **rsi_countertrend:** RSI crosses back above 30 or below 70
- **volatility_breakout:** 20-candle breakout with range at least 1.5 ATR
- **engulfing_reversal:** Current body engulfs the previous opposite-direction body
- **market_structure:** Fresh crossing of the latest confirmed swing
- **liquidity_sweep:** Sweep of the previous 20-candle extreme followed by a close back inside
- **fair_value_gap:** New three-candle imbalance
- **double_top:** Two similar swing highs, bearish displacement and previous-low break

Each strategy/timeframe can enter once per qualifying candle, including while earlier positions remain open. Different strategies can respond to the same market move. Pluto 3/4 Market Structure requires a fresh crossing of the confirmed swing level; earlier Pluto sessions retain the original rule.

Broker tickets are used for reconciliation because broker history timestamps may differ from local time. Unresolved history is not treated as a confirmed close.
