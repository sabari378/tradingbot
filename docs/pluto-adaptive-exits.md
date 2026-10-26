# Pluto adaptive exit experiment — October 20, 2026

Applied mid-session to Pluto 4, with unchanged entry signals, initial stops, risk sizing (0.25% equity, maximum 0.05 lots), spread limit and cutoff at 17:00 America/Indianapolis.

Opt in using --adaptive-exits on backend/demo_catalog_session.py. Default sessions retain fixed 2R exits.

- Liquidity Sweep, Fair Value Gap, Engulfing and Double Top: nearest profitable confirmed opposing swing from 200 completed entry-time bars (two bars either side confirm a swing). Skip new entries when no valid target exists.
- Bollinger and RSI reversion: entry-time 20-bar close average, only when on the profitable side.
- SMA, Donchian, volatility breakout and market structure: remove fixed TP; trail the completed candle close by 2 ATR(14), activated when the executable quote reaches +1 initial R. Stops only tighten. This ATR uses the catalog's simple mean true range.
- Retain initial stops. Existing positions are matched to this session by ticket, symbol and magic. Reconstruct targets using their original signal candle timestamp; never use later candles to choose their initial target.
- Existing trades whose target has already been passed at migration retain their original exits permanently. Broker-distance failures are deferred; old protection remains. Each plan, intent, confirmation and exception is journaled.
- At cutoff, new entries and trailing amendments stop. Broker SL/TP remain; a trend trade can remain open with its latest SL and no TP. Trailing requires the runner and terminal to stay connected.

This session mixes exit policies and includes mid-trade changes. It is exploratory forward observation, not a clean comparison with the prior fixed-2R session. Compare a separate unchanged-entry baseline on subsequent data before judging performance. No time exits or partial closes are enabled.

Verification: 42 targeted tests passed. Full backend run: 114 passed, one unrelated existing /api/v1/strategy-tests endpoint test failed with HTTP 404; reproduced independently.
