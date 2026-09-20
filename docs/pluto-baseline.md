# Pluto ? demo baseline

Snapshot: 2026-09-10T17:23:24.482186-04:00

10 catalog strategies; GOLD.i#; M15, M30, H1.
Evaluation: 42 closed trades; 25 wins; 17 losses; net USD 536.30.

Eight positions open at the snapshot are excluded from this evaluation at the user's request. Their records are retained; no broker position was modified. This is a closed-trade subset, not complete session performance.

| Strategy | Included trades | Net USD |
|---|---:|---:|
| sma_crossover | 1 | 37.43 |
| donchian_breakout | 8 | 141.96 |
| bollinger_reversion | 3 | -52.04 |
| rsi_countertrend | 1 | -22.93 |
| volatility_breakout | 3 | 4.32 |
| engulfing_reversal | 3 | 122.82 |
| market_structure | 17 | 336.06 |
| liquidity_sweep | 5 | -65.85 |
| fair_value_gap | 1 | 34.53 |
| double_top | 0 | 0.00 |

## Next testing proposal

1. Keep Pluto frozen as the reference.
2. Repeat the unchanged rules across ten additional trading days, with results by timeframe and trend/range conditions. This is an initial collection window, not a proof threshold.
3. Compare existing Market Structure against a fresh-cross-only variant on identical data; change only the entry trigger.
4. Evaluate trend filtering for countertrend strategies separately, using rules fixed before looking at validation results.
5. Compare mean net R, drawdown including open positions, profit factor, trade count, and simultaneous exposure. Cluster same-move entries when interpreting evidence.
6. Use chronological development and untouched validation periods, followed by demo forward testing.
7. Define the handling of open trades before the next test starts; carry them to their exits or consistently mark them to market at the cutoff. Do not discard them from a full-performance comparison.

No new testing session has been started.
