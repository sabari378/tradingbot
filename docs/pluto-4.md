# Pluto 4 - September 18, 2026

Demo forward test until 17:00 America/Indianapolis (UTC-04:00).

Yesterday: 44 closed trades, 11 wins, 33 losses, net -$242.41. Liquidity Sweep lost $86.22 over five trades; Engulfing Reversal lost $54.40 over five trades. All five sweeps lacked the directional outer-third close required below. All five engulfings were away from the previous 20-bar extreme.

Changes from Pluto 3:
- Liquidity Sweep: retain sweep setup, require bullish candle closing in top third for BUY or bearish candle closing in bottom third for SELL.
- Engulfing Reversal: retain engulfing setup, require either candle of the two-candle pattern to test or exceed the previous 20 completed bars' low for BUY or high for SELL.
- Other eight unchanged, including Market Structure fresh crossing.

No SL widening, risk increase, additional position caps, or timeframe changes. GOLD.i#, M15/M30/H1, 0.25% equity planned risk per trade, max 0.05 lots, 2R target, spread limit 0.5. All ten strategy toggles remain enabled. Demo-only checks remain enforced. At cutoff no new entries; open positions retain broker SL/TP.

102 backend tests passed. Historical recorded-entry replay: 10 of 44 filled entries filtered, nine losses and one winner, original net -$140.62. Remaining recorded entries net -$101.79, still negative. This is not a portfolio backtest: it excludes additional signals, equity/size changes and execution differences. No parameters were optimized across alternatives. One day's results cannot establish improvement. Forward testing is needed; fitting rules to historical results can overfit (https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).

Evidence: backend/data/pluto/pluto4-entry-review.json and pluto4-replay.json. SCAN records preserve baseline_direction and filtered reasons for comparison. Earlier sessions remain unchanged.
