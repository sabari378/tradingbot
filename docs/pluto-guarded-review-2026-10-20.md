# Pluto guarded forward test — October 20–21, 2026

Broker reconciliation: backend/data/pluto4-20261020-111417/final-review.json. 20 closed trades, 12 wins, 8 losses, net -35.29 USD. Positive outcomes 117.37 USD, negative outcomes -152.66 USD; mean winner 9.78 versus mean loser 19.08 USD. Profit factor 0.77. Includes broker-reported fees, swap and commission.

Four overlapping Donchian/volatility buys across M15/M30 around 14:30 UTC lost 74.89 USD together. Earlier trend winners returned about 0.045 R. Two migrated FVG exits returned about 0.22–0.25 R. This session changed exits mid-trade and does not establish whether adaptive exits outperform fixed 2R.

## adaptive_v2_guarded rules

Retain ten strategy toggles, Pluto 4 signals, GOLD.i#, M15/M30/H1, initial stops, 0.25% maximum planned risk per trade, maximum 0.05 lots, spread limit 0.5.

- One open trade per strategy/timeframe; at most one catalog trend position per symbol and direction across strategies/timeframes. Existing scan order selects among simultaneous signals, a portfolio selection effect.
- New entries limited to 1% total account equity exposure measured from current marks to stops, including unrelated positions and unrealized profit giveback. Missing stops or unavailable calculations block entries.
- Pause entries for the rest of the session after a 1% equity loss from persisted starting equity. Proposed risk must also fit the remaining loss room after existing exposure. This is a session limit, not a calendar-day reset. No automatic flattening; stop slippage, gaps, costs and disconnections can exceed planned limits. Continue exit management during entry pauses.
- Fixed targets must offer at least 1R at entry, otherwise skip; never stretch the target. The threshold is a test constraint, not optimized on today's outcomes.
- Trend exits remain without fixed TP. At +1 initial R, tighten toward the greater of completed-close minus 2 ATR and entry plus spread for BUY; mirrored for SELL. Stops never loosen. The profit floor is gross; costs/slippage can still produce a net loss.
- Bind persistent risk state to the account and recheck positions/budget immediately before submission.
- Separate session folder. Entries and trailing updates end October 21 at 17:00 Indianapolis (UTC−04:00). Open positions retain broker stops, and trend positions may have no TP. PC/MT5/runner must stay connected for updates.

No strategy was disabled based on one day. These are unproven forward-test hypotheses. Review net R, drawdown and rejection logs on later data. Shadow baseline and tick-level counterfactual replay are not implemented.

Validation: 127 backend tests passed; the previously reproduced unrelated /api/v1/strategy-tests endpoint test still fails with 404. New helpers pass Ruff.

Sources: https://www.cmegroup.com/education/courses/building-a-trade-plan/risk-management-and-your-trade-plan and https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
