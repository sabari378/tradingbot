# Chronos Strategy Backtest Report

## Scope

- Broker data: XM MT5, `GOLD.i#`
- Test window: 2026-08-01 00:00 UTC through 2026-09-01 00:00 UTC
- Timeframes: M5, M15, H1
- Enabled signal sets: liquidity, MSS, FVG, and all combinations
- Volume confirmation: tested both disabled and required
- Target: 2R
- Execution: signal on completed candle, entry at next candle open, recorded spread included
- Ambiguous candle policy: stop loss is applied before take profit
- Total configurations: 42; all completed successfully

Signal combinations in this report mean the named detectors were enabled. The current confluence engine does not
require every enabled detector to fire simultaneously; it accepts the available signals when their directions agree.
Consequently, configurations overlap and must not be treated as statistically independent systems.

## Executive Summary

M5 and M15 do not show a robust edge. Only M5 FVG with required volume finished positive in risk-normalized terms,
but its expectancy was just 0.049R with a 1.076 profit factor. Every M15 configuration had negative expectancy.

H1 is the only promising research direction. Thirteen of fourteen H1 configurations were positive, but samples were
only 16 to 55 trades and all came from one calendar month. The leading candidate was H1 MSS with volume confirmation:
18 trades, 50.0% wins, 0.500R expectancy, 2.000 profit factor, and 2R maximum drawdown. This is insufficient for demo
promotion until it passes multi-month walk-forward validation with commission and slippage.

Raw net points are retained for audit purposes but are not used for ranking. Expectancy and drawdown in R are more
comparable when stop distances vary.

## Ranked Candidates

| Rank | Timeframe | Enabled signals | Volume required | Trades | Win rate | Expectancy R | Profit factor | Max DD R | Decision |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | H1 | MSS | Yes | 18 | 50.00% | 0.5000 | 2.0000 | 2 | Validate |
| 2 | H1 | MSS + FVG | Yes | 21 | 47.62% | 0.4499 | 1.8952 | 3 | Validate |
| 3 | H1 | FVG | Yes | 16 | 43.75% | 0.3404 | 1.6369 | 5 | Too few trades |
| 4 | H1 | Liquidity + MSS | Yes | 16 | 43.75% | 0.3125 | 1.5556 | 5 | Too few trades |
| 5 | H1 | Liquidity + FVG | Yes | 21 | 42.86% | 0.3070 | 1.5580 | 7 | Validate |
| 6 | H1 | MSS | No | 21 | 42.86% | 0.3057 | 1.5543 | 4 | Validate |
| 7 | H1 | Liquidity + MSS + FVG | Yes | 19 | 42.11% | 0.2867 | 1.5162 | 6 | Too few trades |
| 8 | H1 | Liquidity + FVG | No | 32 | 37.50% | 0.1458 | 1.2414 | 11 | Validate |
| 9 | H1 | MSS + FVG | No | 27 | 37.04% | 0.1266 | 1.2062 | 6 | Validate |
| 10 | H1 | Liquidity + MSS | No | 22 | 36.36% | 0.1100 | 1.1781 | 6 | Validate |
| 11 | H1 | FVG | No | 26 | 34.62% | 0.0641 | 1.1020 | 7 | Weak |
| 12 | M5 | FVG | Yes | 181 | 34.81% | 0.0490 | 1.0757 | 13 | Marginal |

## Complete Results

### M5

| Enabled signals | Volume | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Liquidity | No | 540 | 139 | 401 | 25.74% | -138.5001 | -0.2278 | 0.6933 | 131 |
| Liquidity | Yes | 242 | 65 | 177 | 26.86% | -95.0126 | -0.1942 | 0.7345 | 60 |
| MSS | No | 488 | 134 | 354 | 27.46% | 156.5161 | -0.1799 | 0.7520 | 97 |
| MSS | Yes | 276 | 79 | 197 | 28.62% | 258.9743 | -0.1377 | 0.8061 | 61 |
| FVG | No | 396 | 126 | 270 | 31.82% | 117.2115 | -0.0500 | 0.9266 | 34 |
| FVG | Yes | 181 | 63 | 118 | 34.81% | 133.6762 | 0.0490 | 1.0757 | 13 |
| Liquidity + MSS | No | 525 | 136 | 389 | 25.90% | 54.1138 | -0.2263 | 0.6946 | 133 |
| Liquidity + MSS | Yes | 286 | 85 | 201 | 29.72% | 290.2392 | -0.1049 | 0.8499 | 59 |
| Liquidity + FVG | No | 467 | 151 | 316 | 32.33% | 127.5996 | -0.0338 | 0.9500 | 44 |
| Liquidity + FVG | Yes | 246 | 81 | 165 | 32.93% | 142.6189 | -0.0087 | 0.9870 | 30 |
| MSS + FVG | No | 518 | 150 | 368 | 28.96% | 365.3447 | -0.1348 | 0.8103 | 79 |
| MSS + FVG | Yes | 288 | 89 | 199 | 30.90% | 421.2441 | -0.0695 | 0.8989 | 47 |
| Liquidity + MSS + FVG | No | 519 | 146 | 373 | 28.13% | 274.6623 | -0.1596 | 0.7780 | 100 |
| Liquidity + MSS + FVG | Yes | 283 | 88 | 195 | 31.10% | 412.0006 | -0.0637 | 0.9071 | 47 |

### M15

| Enabled signals | Volume | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Liquidity | No | 177 | 54 | 123 | 30.51% | 237.1500 | -0.0896 | 0.8711 | 22 |
| Liquidity | Yes | 87 | 26 | 61 | 29.89% | 167.2973 | -0.1034 | 0.8525 | 15 |
| MSS | No | 98 | 29 | 69 | 29.59% | 399.0635 | -0.1296 | 0.8159 | 22 |
| MSS | Yes | 50 | 14 | 36 | 28.00% | 341.7912 | -0.1940 | 0.7306 | 19 |
| FVG | No | 45 | 14 | 31 | 31.11% | 443.0759 | -0.1044 | 0.8484 | 15 |
| FVG | Yes | 39 | 13 | 26 | 33.33% | 369.7213 | -0.0436 | 0.9346 | 13 |
| Liquidity + MSS | No | 116 | 37 | 79 | 31.90% | 449.9538 | -0.0578 | 0.9152 | 17 |
| Liquidity + MSS | Yes | 63 | 18 | 45 | 28.57% | 301.0733 | -0.1698 | 0.7622 | 17 |
| Liquidity + FVG | No | 143 | 47 | 96 | 32.87% | 273.4375 | -0.0259 | 0.9615 | 13 |
| Liquidity + FVG | Yes | 124 | 38 | 86 | 30.65% | 209.3681 | -0.0944 | 0.8640 | 18 |
| MSS + FVG | No | 125 | 37 | 88 | 29.60% | 411.7665 | -0.1256 | 0.8216 | 21 |
| MSS + FVG | Yes | 57 | 16 | 41 | 28.07% | 303.2327 | -0.1877 | 0.7390 | 21 |
| Liquidity + MSS + FVG | No | 140 | 40 | 100 | 28.57% | 404.7253 | -0.1550 | 0.7830 | 27 |
| Liquidity + MSS + FVG | Yes | 70 | 21 | 49 | 30.00% | 280.8630 | -0.1243 | 0.8224 | 19 |

### H1

| Enabled signals | Volume | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Liquidity | No | 55 | 19 | 36 | 34.55% | 264.8022 | 0.0364 | 1.0556 | 9 |
| Liquidity | Yes | 29 | 9 | 20 | 31.03% | 173.4172 | -0.0690 | 0.9000 | 6 |
| MSS | No | 21 | 9 | 12 | 42.86% | 279.7869 | 0.3057 | 1.5543 | 4 |
| MSS | Yes | 18 | 9 | 9 | 50.00% | 334.1229 | 0.5000 | 2.0000 | 2 |
| FVG | No | 26 | 9 | 17 | 34.62% | 290.0653 | 0.0641 | 1.1020 | 7 |
| FVG | Yes | 16 | 7 | 9 | 43.75% | 289.8135 | 0.3404 | 1.6369 | 5 |
| Liquidity + MSS | No | 22 | 8 | 14 | 36.36% | 240.8101 | 0.1100 | 1.1781 | 6 |
| Liquidity + MSS | Yes | 16 | 7 | 9 | 43.75% | 331.5105 | 0.3125 | 1.5556 | 5 |
| Liquidity + FVG | No | 32 | 12 | 20 | 37.50% | 288.6282 | 0.1458 | 1.2414 | 11 |
| Liquidity + FVG | Yes | 21 | 9 | 12 | 42.86% | 330.3443 | 0.3070 | 1.5580 | 7 |
| MSS + FVG | No | 27 | 10 | 17 | 37.04% | 258.2931 | 0.1266 | 1.2062 | 6 |
| MSS + FVG | Yes | 21 | 10 | 11 | 47.62% | 323.2347 | 0.4499 | 1.8952 | 3 |
| Liquidity + MSS + FVG | No | 27 | 9 | 18 | 33.33% | 224.6931 | 0.0155 | 1.0238 | 8 |
| Liquidity + MSS + FVG | Yes | 19 | 8 | 11 | 42.11% | 320.6223 | 0.2867 | 1.5162 | 6 |

## Decision

Do not promote any configuration to live or unattended demo execution from this report. Advance H1 MSS with volume,
H1 MSS plus FVG with volume, and H1 MSS without volume into walk-forward validation. Retain M5 FVG with volume as a
lower-priority robustness check because its large sample has only a marginal edge. Reject the other M5 configurations
and all M15 configurations in their current form.

The next validation should use several non-overlapping monthly windows, enforce a minimum of 100 out-of-sample trades,
add commission and configurable slippage, and compare strict AND-confluence rules against the current directional-agreement
behavior. No parameter should be selected using the final holdout window.
