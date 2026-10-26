# Demo strategy monitor

Updated: 2026-10-20T22:13:54.693129-04:00

Balance: $9954.24; equity: $9954.24; broker positions: 0.

| Strategy | Entries | Open | Closed | Wins | Losses | Realized USD | Floating USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| sma_crossover | 2 | 0 | 2 | 0 | 2 | -39.26 | 0 |
| donchian_breakout | 3 | 0 | 3 | 1 | 2 | -36.85 | 0 |
| bollinger_reversion | 3 | 0 | 3 | 1 | 2 | -10.45 | 0 |
| rsi_countertrend | 3 | 0 | 3 | 3 | 0 | 52.49 | 0 |
| volatility_breakout | 3 | 0 | 3 | 1 | 2 | -36.8 | 0 |
| engulfing_reversal | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| market_structure | 2 | 0 | 2 | 2 | 0 | 3.96 | 0 |
| liquidity_sweep | 1 | 0 | 1 | 1 | 0 | 9.22 | 0 |
| fair_value_gap | 3 | 0 | 3 | 3 | 0 | 22.4 | 0 |
| double_top | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Individual trades

| Ticket | Strategy | TF | Side | Lots | Status | Realized USD | Floating USD | Exit |
|---|---|---|---|---:|---|---:|---:|---|
| 1062043944 | sma_crossover | M15 | BUY | 0.01 | CLOSED | -17.78 | 0 | SL |
| 1062237234 | sma_crossover | M15 | SELL | 0.04 | CLOSED | -21.48 | 0 | SL |
| 1061817102 | donchian_breakout | M15 | BUY | 0.01 | CLOSED | 0.63 | 0 | SL |
| 1061922182 | donchian_breakout | M15 | BUY | 0.01 | CLOSED | -17.83 | 0 | SL |
| 1061922193 | donchian_breakout | M30 | BUY | 0.01 | CLOSED | -19.65 | 0 | SL |
| 1061817104 | bollinger_reversion | M15 | SELL | 0.02 | CLOSED | -24.36 | 0 | SL |
| 1061878760 | bollinger_reversion | M15 | SELL | 0.01 | CLOSED | -14.15 | 0 | SL |
| 1061922199 | bollinger_reversion | M30 | SELL | 0.01 | CLOSED | 28.06 | 0 | TP |
| 1061953340 | rsi_countertrend | M15 | SELL | 0.01 | CLOSED | 23.42 | 0 | TP |
| 1062194202 | rsi_countertrend | M15 | BUY | 0.03 | CLOSED | 13.68 | 0 | TP |
| 1062211225 | rsi_countertrend | M15 | BUY | 0.03 | CLOSED | 15.39 | 0 | TP |
| 1061817107 | volatility_breakout | M15 | BUY | 0.01 | CLOSED | 0.61 | 0 | SL |
| 1061922186 | volatility_breakout | M15 | BUY | 0.01 | CLOSED | -17.67 | 0 | SL |
| 1061922211 | volatility_breakout | M30 | BUY | 0.01 | CLOSED | -19.74 | 0 | SL |
| 1061817110 | market_structure | M15 | BUY | 0.01 | CLOSED | 0.63 | 0 | SL |
| 1061850779 | market_structure | M30 | BUY | 0.01 | CLOSED | 3.33 | 0 | SL |
| 1061587411 | liquidity_sweep | H1 | BUY | 0.01 | CLOSED | 9.22 | 0 | TP |
| 1061587409 | fair_value_gap | M15 | BUY | 0.01 | CLOSED | 3.13 | 0 | TP |
| 1061595339 | fair_value_gap | M30 | BUY | 0.01 | CLOSED | 2.88 | 0 | TP |
| 1061998866 | fair_value_gap | M15 | SELL | 0.01 | CLOSED | 16.39 | 0 | TP |

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
