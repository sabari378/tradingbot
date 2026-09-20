# Internet-Derived Strategy Backtest Report

## Scope

Chronos tested ten deterministic candle-based strategy families commonly described in trading education and research.
The implementations use explicit rules rather than discretionary chart interpretation.

- Broker data: XM MT5 `GOLD.i#`
- M15 and H1 period: 2025-09-01 through 2026-09-01 (one year)
- M5 period: 2026-03-01 through 2026-09-01 (six months)
- M5 was shortened because a full year exceeded the 100,000-candle API limit
- Exit target: 2R
- Stops: 1.5 ATR, except liquidity/FVG structure stops and pattern-defined double-top stops
- Entry: next candle open after a completed signal candle
- Costs: recorded XM spread included; commission and additional slippage excluded
- Same-bar ambiguity: stop loss applied first
- Runs: 30 of 30 completed after the M5 period adjustment

## Strategy Definitions

| Strategy | Deterministic rule used |
|---|---|
| SMA crossover | Fresh 20-period SMA cross of the 50-period SMA |
| Donchian breakout | Close beyond the previous 20-candle high or low |
| Bollinger reversion | Fresh close beyond a 20-period mean by two population standard deviations |
| RSI countertrend | RSI(14) crosses back above 30 or below 70 |
| Volatility breakout | 20-candle breakout with current range at least 1.5 ATR |
| Engulfing reversal | Current real body fully engulfs the previous opposite-color body |
| Market structure | Close breaks the latest confirmed swing high or swing low |
| Liquidity sweep | Price pierces a 20-candle extreme and closes back through it |
| Fair value gap | Fresh three-candle bullish or bearish imbalance |
| Double top | Two ATR-tolerant swing peaks followed by bearish displacement and a previous-low break |

Trend and countertrend are broad recognized categories in CME trading education. Time-series momentum is a canonical
trend implementation, while pattern recognition, mean reversion, carry, and relative value are recognized systematic
families. Sources: https://www.cmegroup.com/education/courses/trading-and-analysis/trend-vs-anti-trend and
https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing

## Executive Result

H1 produced the most credible candidates. The H1 SMA crossover led the study with 112 trades, 43.75% wins, 0.3125R
expectancy, a 1.5556 profit factor, and 7R maximum drawdown. H1 Donchian breakout, engulfing reversal, market structure,
and volatility breakout were also positive, though materially weaker.

Shorter timeframes did not produce a strong edge. A few M5 and M15 strategies were slightly positive, but profit
factors near 1.0 leave insufficient margin for commission, slippage, or changed market conditions. Mean reversion,
liquidity sweep, standalone FVG, and double top failed in their present forms.

## Ranked Positive Results

| Rank | Strategy | TF | Trades | Win rate | Expectancy R | Profit factor | Max DD R | Assessment |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | SMA crossover | H1 | 112 | 43.75% | 0.3125 | 1.5556 | 7 | Primary candidate |
| 2 | Donchian breakout | H1 | 286 | 38.11% | 0.1369 | 1.2212 | 18 | Validate |
| 3 | Engulfing reversal | H1 | 292 | 36.99% | 0.1119 | 1.1783 | 27 | Validate cautiously |
| 4 | Market structure | H1 | 432 | 36.57% | 0.0930 | 1.1466 | 12 | Validate |
| 5 | Volatility breakout | H1 | 210 | 34.76% | 0.0429 | 1.0657 | 13 | Marginal |
| 6 | Engulfing reversal | M15 | 1,040 | 35.00% | 0.0487 | 1.0749 | 49 | Marginal/high drawdown |
| 7 | SMA crossover | M5 | 740 | 34.59% | 0.0378 | 1.0579 | 43 | Marginal |
| 8 | Market structure | M15 | 1,592 | 34.11% | 0.0236 | 1.0358 | 41 | Reject after costs |
| 9 | SMA crossover | M15 | 443 | 34.09% | 0.0226 | 1.0342 | 28 | Reject after costs |
| 10 | Volatility breakout | M15 | 852 | 34.04% | 0.0218 | 1.0330 | 32 | Reject after costs |
| 11 | Engulfing reversal | M5 | 1,619 | 33.91% | 0.0161 | 1.0244 | 58 | Reject after costs |
| 12 | Donchian breakout | M15 | 1,170 | 33.59% | 0.0060 | 1.0091 | 32 | Reject after costs |

## Complete Results

### M5 (Six Months)

| Strategy | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA crossover | 740 | 256 | 484 | 34.59% | 364.7439 | 0.0378 | 1.0579 | 43 |
| Donchian breakout | 1,728 | 558 | 1,170 | 32.29% | -245.7154 | -0.0308 | 0.9545 | 94 |
| Bollinger reversion | 1,498 | 472 | 1,026 | 31.51% | -767.7539 | -0.0547 | 0.9201 | 100 |
| RSI countertrend | 1,343 | 446 | 897 | 33.21% | -401.5989 | -0.0031 | 0.9953 | 42 |
| Volatility breakout | 1,143 | 378 | 765 | 33.07% | 260.6882 | -0.0079 | 0.9882 | 73 |
| Engulfing reversal | 1,619 | 549 | 1,070 | 33.91% | 544.0743 | 0.0161 | 1.0244 | 58 |
| Market structure | 2,368 | 773 | 1,595 | 32.64% | 321.7486 | -0.0210 | 0.9688 | 128 |
| Liquidity sweep | 2,982 | 773 | 2,209 | 25.92% | -265.6941 | -0.2223 | 0.6999 | 670 |
| Fair value gap | 1,875 | 530 | 1,345 | 28.27% | -766.4150 | -0.1530 | 0.7868 | 314 |
| Double top | 176 | 56 | 120 | 31.82% | -40.5180 | -0.0455 | 0.9333 | 27 |

### M15 (One Year)

| Strategy | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA crossover | 443 | 151 | 292 | 34.09% | 123.2239 | 0.0226 | 1.0342 | 28 |
| Donchian breakout | 1,170 | 393 | 777 | 33.59% | -431.0561 | 0.0060 | 1.0091 | 32 |
| Bollinger reversion | 1,003 | 318 | 685 | 31.70% | -1346.3279 | -0.0489 | 0.9285 | 90 |
| RSI countertrend | 927 | 275 | 652 | 29.67% | -2636.3564 | -0.1111 | 0.8420 | 108 |
| Volatility breakout | 852 | 290 | 562 | 34.04% | 331.6464 | 0.0218 | 1.0330 | 32 |
| Engulfing reversal | 1,040 | 364 | 676 | 35.00% | 1602.5846 | 0.0487 | 1.0749 | 49 |
| Market structure | 1,592 | 543 | 1,049 | 34.11% | 309.9364 | 0.0236 | 1.0358 | 41 |
| Liquidity sweep | 2,059 | 532 | 1,527 | 25.84% | -1177.5082 | -0.2253 | 0.6962 | 465 |
| Fair value gap | 1,340 | 391 | 949 | 29.18% | 393.3786 | -0.1259 | 0.8222 | 187 |
| Double top | 130 | 42 | 88 | 32.31% | 462.1798 | -0.0308 | 0.9545 | 15 |

### H1 (One Year)

| Strategy | Trades | Wins | Losses | Win rate | Net points | Expectancy R | Profit factor | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMA crossover | 112 | 49 | 63 | 43.75% | 1250.4864 | 0.3125 | 1.5556 | 7 |
| Donchian breakout | 286 | 109 | 177 | 38.11% | 800.0782 | 0.1369 | 1.2212 | 18 |
| Bollinger reversion | 258 | 75 | 183 | 29.07% | -1222.0096 | -0.1279 | 0.8197 | 45 |
| RSI countertrend | 242 | 81 | 161 | 33.47% | -89.0796 | -0.0034 | 0.9949 | 15 |
| Volatility breakout | 210 | 73 | 137 | 34.76% | -35.2832 | 0.0429 | 1.0657 | 13 |
| Engulfing reversal | 292 | 108 | 184 | 36.99% | 1542.0646 | 0.1119 | 1.1783 | 27 |
| Market structure | 432 | 158 | 274 | 36.57% | 916.4932 | 0.0930 | 1.1466 | 12 |
| Liquidity sweep | 515 | 147 | 368 | 28.54% | -308.0396 | -0.1437 | 0.7989 | 83 |
| Fair value gap | 400 | 116 | 284 | 29.00% | 522.4225 | -0.1283 | 0.8188 | 73 |
| Double top | 35 | 7 | 28 | 20.00% | -179.9924 | -0.4000 | 0.5000 | 14 |

## Excluded Internet Strategy Families

Chronos did not simulate carry, value, fundamental, news-event, sentiment, statistical arbitrage, cross-venue arbitrage,
market making, options volatility, or machine-learning strategies. The current XM single-symbol candle feed lacks the
fundamental releases, historical news timestamps, option chains, order books, synchronized multi-asset data, or trained
models required to test those strategies without inventing evidence.

## Recommendation

Do not promote any result directly to trading. Advance H1 SMA crossover as the primary hypothesis and H1 Donchian,
engulfing, and market-structure strategies as secondary hypotheses. Run anchored walk-forward tests with monthly and
quarterly slices, add commission and slippage, and reserve the most recent period as an untouched holdout. A candidate
should remain positive across regimes and nearby parameters rather than merely winning this one test window.
