import json
from datetime import datetime, timezone
from pathlib import Path

from nirv.core.config import get_settings
from nirv.services.strategy_controls import enabled_strategies
from nirv.strategies.catalog import CATALOG_STRATEGIES

DESCRIPTIONS = {
 'sma_crossover': 'Fresh cross of the 20- and 50-period simple moving averages.',
 'donchian_breakout': 'Close beyond the previous 20-candle high or low.',
 'bollinger_reversion': 'Countertrend entry on a fresh close outside a two-standard-deviation band.',
 'rsi_countertrend': 'RSI crosses back above 30 or below 70.',
 'volatility_breakout': '20-candle breakout with candle range at least 1.5 ATR.',
 'engulfing_reversal': 'A candle body engulfs the preceding opposite-direction body.',
 'market_structure': 'Close beyond the latest confirmed swing; later candles can repeat the signal.',
 'liquidity_sweep': 'Sweep of a prior high or low followed by a close back inside.',
 'fair_value_gap': 'A new three-candle price imbalance.',
 'double_top': 'Two similar peaks, bearish displacement and a previous-low break.',
}


def read_events(path):
    rows = []
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def strategy_dashboard():
    root = Path(get_settings().data_dir)
    enabled = enabled_strategies()
    trades = {}
    sessions = []
    for folder in sorted(root.glob('*')):
        if not folder.is_dir() or not (folder / 'supervisor.jsonl').exists():
            continue
        journal_files = [folder / f'{s}-demo.jsonl' for s in CATALOG_STRATEGIES]
        if not any(p.exists() for p in journal_files):
            continue
        sessions.append({'id': folder.name, 'name': ('Pluto 4' if 'pluto4' in folder.name else 'Pluto 3' if 'pluto3' in folder.name else 'Pluto repeat' if 'repeat' in folder.name else 'Pluto') + ' · ' + folder.name})
        snapshot = {}
        snapshot_at = None
        snapshot_file = folder / 'analysis-latest.json'
        if snapshot_file.exists():
            try:
                content = json.loads(snapshot_file.read_text())
                snapshot = {str(t['ticket']): t for t in content['trades']}
                snapshot_at = content['checked_at']
            except (ValueError, KeyError):
                pass
        for strategy, path in zip(CATALOG_STRATEGIES, journal_files):
            if not path.exists():
                continue
            reasons = {}
            closed = {}
            rows = read_events(path)
            for row in rows:
                if row['event'] == 'CLOSED':
                    closed[str(row['ticket'])] = row
            for row in rows:
                if row['event'] == 'SCAN':
                    reasons[row['timeframe']] = row.get('confluences', [])
                if row['event'] != 'FILLED':
                    continue
                ticket = str(row['ticket'])
                cached = snapshot.get(ticket, {})
                closure = closed.get(ticket)
                trades[ticket] = {
                    'ticket': ticket, 'session': folder.name, 'strategy': strategy,
                    'timeframe': row['timeframe'], 'direction': row['direction'],
                    'volume': row['volume'], 'entry': row['entry'],
                    'sl': row['stop_loss'], 'tp': row['take_profit'], 'opened_at': row['timestamp'],
                    'status': 'CLOSED' if closure else cached.get('status', 'UNRESOLVED'),
                    'realized': closure['net_pnl'] if closure else cached.get('realized'),
                    'floating': 0 if closure else cached.get('floating'),
                    'exit': cached.get('exit'), 'exit_reason': cached.get('exit_reason'),
                    'reasons': reasons.get(row['timeframe'], []), 'updated_at': snapshot_at,
                }
    live = False
    error = None
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize(timeout=5000):
            raise RuntimeError('MT5 connection unavailable; showing recorded results')
        try:
            positions = mt5.positions_get()
            if positions is None:
                raise RuntimeError('Positions unavailable; showing recorded results')
            active = {str(p.ticket): p for p in positions}
            now = datetime.now(timezone.utc).isoformat()
            for ticket, trade in trades.items():
                deals = mt5.history_deals_get(position=int(ticket))
                if deals is None:
                    error = 'Some trade history could not be refreshed'
                    continue
                net = round(sum(d.profit + d.commission + d.swap + d.fee for d in deals), 2)
                if ticket in active:
                    p = active[ticket]
                    trade.update(status='OPEN', realized=net, floating=round(p.profit+p.swap, 2), sl=p.sl, tp=p.tp,
                                 current=p.price_current, updated_at=now)
                elif deals and any(d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY) for d in deals):
                    trade.update(status='CLOSED', realized=net, floating=0, exit=deals[-1].price,
                                 exit_reason={mt5.DEAL_REASON_SL:'SL', mt5.DEAL_REASON_TP:'TP'}.get(deals[-1].reason, 'Other'),
                                 updated_at=now)
                else:
                    trade.update(status='UNRESOLVED', floating=None)
                    error = 'Some trades have not been reconciled'
            live = error is None
        finally:
            mt5.shutdown()
    except (ImportError, RuntimeError) as exc:
        error = str(exc)
    return {
        'strategies': [{'id': s, 'name': s.replace('_', ' ').title(), 'description': DESCRIPTIONS[s],
                        'enabled': enabled[s]} for s in CATALOG_STRATEGIES],
        'sessions': sessions, 'trades': sorted(trades.values(), key=lambda t:t['opened_at'], reverse=True),
        'live': live, 'warning': error, 'checked_at': datetime.now(timezone.utc).isoformat(),
    }

