"""Ten isolated catalog demo sessions, with serialized account-wide risk checks."""
import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from nirv.strategies.adaptive_exits import POLICY, exit_target, manage_exits, round_target, valid_levels
from nirv.strategies.session_guards import check_overlap, check_target_reward, entry_budget
from nirv.services.strategy_controls import strategy_enabled
from nirv.strategies.market_structure import fresh_bos_context
from nirv.market.candles import Candle
from nirv.strategies.catalog import CATALOG_STRATEGIES, evaluate_catalog_strategy, evaluate_pluto4_strategy

TIMEFRAMES = ('M15', 'M30', 'H1')
MAGIC_BASE = 1302020000


def emit(path, event, **fields):
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(dict(event=event, timestamp=datetime.now(timezone.utc).isoformat(), **fields)) + '\n')
        handle.flush()


def seen_signals(path):
    if not path.exists():
        return set()
    return {r['signal_key'] for line in path.read_text().splitlines() if line.strip()
            for r in [json.loads(line)] if r['event'] == 'SIGNAL_CONSUMED'}


def select_volume(mt5, symbol, side, entry, stop, info, budget, max_volume=.05):
    """Use broker profit calculation in account currency; never round risk up."""
    if budget <= 0:
        raise ValueError('open_risk_budget_exhausted')
    count = int(round((min(info.volume_max, max_volume) - info.volume_min) / info.volume_step))
    for step in range(count, -1, -1):
        volume = round(info.volume_min + step * info.volume_step, 8)
        if volume > min(info.volume_max, max_volume) + 1e-9:
            continue
        pnl = mt5.order_calc_profit(side, symbol, volume, entry, stop)
        if pnl is None or not math.isfinite(pnl):
            raise ValueError('broker_risk_calculation_failed')
        if abs(pnl) <= budget + 1e-8:
            return volume, abs(pnl)
    raise ValueError('minimum_lot_exceeds_risk_budget')


def open_risk(mt5, positions):
    total = 0.0
    for p in positions:
        if not p.sl:
            return math.inf
        pnl = mt5.order_calc_profit(p.type, p.symbol, p.volume, p.price_open, p.sl)
        if pnl is None or not math.isfinite(pnl):
            return math.inf
        total += max(0, -pnl)
    return total


def check_account(mt5):
    account, terminal = mt5.account_info(), mt5.terminal_info()
    if not account or not terminal or not terminal.connected:
        raise ValueError('terminal_disconnected')
    if account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO or account.currency != 'USD':
        raise ValueError('USD_demo_account_required')
    if account.margin_mode != mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:
        raise ValueError('hedging_account_required_for_strategy_isolation')
    if not (account.trade_allowed and account.trade_expert and terminal.trade_allowed) or terminal.tradeapi_disabled:
        raise ValueError('autotrading_disabled')
    return account


def run(args, mt5):
    end = datetime.fromisoformat(args.end_at)
    if end.tzinfo is None:
        raise ValueError('end_at_requires_timezone')
    end_timestamp = end.timestamp()
    if end_timestamp <= time.time():
        raise ValueError('cutoff_has_passed')
    folder = Path(args.output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    supervisor = folder / 'supervisor.jsonl'
    journals = {s: folder / (s + '-demo.jsonl') for s in CATALOG_STRATEGIES}
    seen = {s: seen_signals(p) for s, p in journals.items()}
    halt_file = folder / 'orders-halted.txt'
    guarded = getattr(args, 'guarded', False)
    policy = 'adaptive_v2_guarded' if guarded else POLICY
    risk_file = folder / 'risk-state.json'
    risk_halt = folder / 'risk-entries-halted.txt'
    risk_state = json.loads(risk_file.read_text()) if guarded and risk_file.exists() else None
    for s, path in journals.items():
        emit(path, 'CATALOG_STARTED', strategy=s, symbol=args.symbol, timeframes=TIMEFRAMES,
             end_at=end.isoformat(), risk_dollars=args.risk_dollars, total_risk_dollars=args.total_risk_dollars,
             risk_reward=None if getattr(args, 'adaptive_exits', False) else 2,
             exit_policy=policy if getattr(args, 'adaptive_exits', False) else 'fixed_2R',
             max_positions=None, variant=getattr(args, 'variant', 'pluto'))
    known = {}
    for path in journals.values():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row['event'] == 'FILLED':
                known[int(row['ticket'])] = (path, row['planned_risk'])
            elif row['event'] == 'CLOSED':
                known.pop(int(row['ticket']), None)
    with httpx.Client(timeout=10) as client:
        while time.time() < end_timestamp:
            try:
                response = client.get(args.backend + '/api/v1/controls/emergency-stop')
                response.raise_for_status()
                if response.json().get('active'):
                    emit(supervisor, 'EMERGENCY_STOP')
                    break
                if not mt5.initialize(timeout=5000):
                    raise ValueError('MT5_initialize_failed')
                account = check_account(mt5)
                if guarded:
                    if risk_state is None:
                        risk_state = dict(start_equity=account.equity, account_login=account.login,
                                          account_server=account.server, policy=policy,
                                          started_at=datetime.now(timezone.utc).isoformat())
                        temp = risk_file.with_suffix('.tmp')
                        temp.write_text(json.dumps(risk_state, indent=2))
                        temp.replace(risk_file)
                    if account.login != risk_state['account_login'] or account.server != risk_state['account_server']:
                        raise ValueError('guard_account_changed')
                    if account.equity <= risk_state['start_equity'] * .99 and not risk_halt.exists():
                        risk_halt.write_text('1% session equity loss reached; entries paused until operator review.')
                        emit(supervisor, 'RISK_ENTRIES_HALTED', equity=account.equity, **risk_state)
                positions = mt5.positions_get()
                if positions is None:
                    raise ValueError('positions_unavailable')
                active = {p.ticket for p in positions}
                for ticket, (journal, planned_risk) in list(known.items()):
                    if ticket not in active:
                        deals = mt5.history_deals_get(position=ticket)
                        if deals and any(d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY) for d in deals):
                            net = sum(d.profit + d.commission + d.swap + d.fee for d in deals)
                            emit(journal, 'CLOSED', ticket=ticket, net_pnl=net, pnl_r=net/planned_risk,
                                 deals=[dict(ticket=d.ticket, price=d.price, entry=d.entry, reason=d.reason) for d in deals])
                            del known[ticket]
                info = mt5.symbol_info(args.symbol)
                if not info or not info.visible:
                    raise ValueError('symbol_unavailable')
                if getattr(args, 'adaptive_exits', False) and not halt_file.exists():
                    def authorize_exit():
                        exit_account = check_account(mt5)
                        if guarded and (exit_account.login != risk_state['account_login'] or
                                        exit_account.server != risk_state['account_server']):
                            raise ValueError('guard_account_changed')
                        control = client.get(args.backend + '/api/v1/controls/emergency-stop')
                        control.raise_for_status()
                        return not control.json().get('active') and time.time() < end_timestamp
                    manage_exits(mt5, journals, args.symbol, emit, authorize_exit,
                                 policy=policy, protect_profit=guarded)
                emit(supervisor, 'HEARTBEAT', equity=account.equity, positions=len(positions),
                     open_risk=open_risk(mt5, positions), orders_halted=halt_file.exists(),
                     entries_risk_halted=risk_halt.exists(), exit_policy=policy if guarded else None)
                for tf_index, tf in enumerate(TIMEFRAMES):
                    bars = mt5.copy_rates_from_pos(args.symbol, getattr(mt5, 'TIMEFRAME_' + tf), 1, 200)
                    if bars is None or len(bars) < 51:
                        raise ValueError('insufficient_candles_' + tf)
                    candles = [Candle(float(b['open']), float(b['high']), float(b['low']), float(b['close']),
                                      float(b['tick_volume'])) for b in bars]
                    key = tf + ':' + str(int(bars[-1]['time']))
                    for index, strategy in enumerate(CATALOG_STRATEGIES):
                        if key in seen[strategy] or time.time() >= end_timestamp:
                            continue
                        path = journals[strategy]
                        # Persist before any order attempt, including a possible uncertain response.
                        emit(path, 'SIGNAL_CONSUMED', signal_key=key, timeframe=tf)
                        seen[strategy].add(key)
                        fresh = getattr(args, 'variant', 'pluto') in ('pluto3', 'pluto4') and strategy == 'market_structure'
                        decision = evaluate_catalog_strategy(strategy, candles, risk_reward=2, fresh_structure=fresh)
                        baseline_direction = decision.confluence.direction
                        if getattr(args, 'variant', 'pluto') == 'pluto4':
                            decision = evaluate_pluto4_strategy(strategy, candles, risk_reward=2)
                        direction = decision.confluence.direction
                        emit(path, 'SCAN', timeframe=tf, direction=direction, baseline_direction=baseline_direction, confluences=decision.confluence.confluences,
                             structure_context=fresh_bos_context(candles) if fresh else None)
                        if not direction or halt_file.exists() or risk_halt.exists() or not strategy_enabled(strategy):
                            continue
                        try:
                            account = check_account(mt5)
                            tick = mt5.symbol_info_tick(args.symbol)
                            if tick is None or tick.ask <= tick.bid or tick.bid <= 0:
                                raise ValueError('invalid_quote')
                            if tick.ask - tick.bid > args.max_spread:
                                raise ValueError('spread_exceeds_limit')
                            positions = mt5.positions_get()
                            if positions is None:
                                raise ValueError('positions_unavailable')
                            budget = account.equity * .0025
                            if args.risk_dollars:
                                budget = min(budget, args.risk_dollars)
                            if args.total_risk_dollars:
                                budget = min(budget, args.total_risk_dollars - open_risk(mt5, positions))
                            side = mt5.ORDER_TYPE_BUY if direction == 'BUY' else mt5.ORDER_TYPE_SELL
                            magic = MAGIC_BASE+index*10+tf_index
                            if guarded:
                                check_overlap(positions, strategy, args.symbol, side, magic)
                                budget = min(budget, entry_budget(mt5, positions, account.equity,
                                                                 risk_state['start_equity']))
                            entry = tick.ask if direction == 'BUY' else tick.bid
                            raw_stop = float(decision.stop_loss)
                            # Broker candles use Bid; a short exits at Ask.
                            if direction == 'SELL':
                                raw_stop += tick.ask - tick.bid
                            step = info.trade_tick_size
                            stop = (math.floor(raw_stop / step) if direction == 'BUY' else math.ceil(raw_stop / step)) * step
                            stop = round(stop, info.digits)
                            distance = entry - stop if direction == 'BUY' else stop - entry
                            if distance <= 0:
                                raise ValueError('invalid_stop_side')
                            target = round(round((entry + (2*distance if direction == 'BUY' else -2*distance))/step)*step, info.digits)
                            exit_rule = 'fixed_2R'
                            if getattr(args, 'adaptive_exits', False):
                                target, exit_rule = exit_target(strategy, candles, direction, entry)
                                target = round_target(target, info)
                                if target and (target <= entry if direction == 'BUY' else target >= entry):
                                    raise ValueError('adaptive_exit_rounded_target_not_profitable')
                                if not valid_levels(direction, stop, target, tick, info):
                                    raise ValueError('adaptive_exit_invalid_broker_distance')
                            if guarded:
                                check_target_reward(direction, entry, stop, target)
                            volume, risk = select_volume(mt5, args.symbol, side, entry, stop, info, budget)
                            request = dict(action=mt5.TRADE_ACTION_DEAL, symbol=args.symbol, type=side,
                                           volume=volume, price=entry, sl=stop, tp=target, deviation=20,
                                           magic=magic, comment=f'catalog:{index}:{tf}',
                                           type_time=mt5.ORDER_TIME_GTC, type_filling=mt5.ORDER_FILLING_IOC)
                            checked = mt5.order_check(request)
                            if checked is None or checked.retcode != 0:
                                raise ValueError('order_check: ' + str(getattr(checked, 'comment', mt5.last_error())))
                            control = client.get(args.backend + '/api/v1/controls/emergency-stop')
                            control.raise_for_status()
                            if control.json().get('active') or time.time() >= end_timestamp or not strategy_enabled(strategy):
                                continue
                            if guarded:
                                latest = check_account(mt5)
                                if latest.login != risk_state['account_login'] or latest.server != risk_state['account_server']:
                                    raise ValueError('guard_account_changed')
                                latest_positions = mt5.positions_get()
                                if latest_positions is None:
                                    raise ValueError('positions_unavailable')
                                check_overlap(latest_positions, strategy, args.symbol, side, magic)
                                if risk > entry_budget(mt5, latest_positions, latest.equity,
                                                       risk_state['start_equity']) + 1e-8:
                                    raise ValueError('guard_risk_changed_before_order')
                            emit(path, 'ORDER_INTENT', signal_key=key, timeframe=tf, request=request, planned_risk=risk,
                                 exit_policy=policy if getattr(args, 'adaptive_exits', False) else 'fixed_2R', exit_rule=exit_rule)
                            result = mt5.order_send(request)
                            if result is None or result.retcode in (mt5.TRADE_RETCODE_TIMEOUT, mt5.TRADE_RETCODE_CONNECTION):
                                halt_file.write_text('Uncertain order result; reconcile broker history before resuming orders.')
                                emit(path, 'ORDER_UNCERTAIN', signal_key=key)
                                continue
                            if result.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_DONE_PARTIAL):
                                raise ValueError('order_rejected: ' + result.comment)
                            ticket = int(result.order)
                            emit(path, 'FILLED', timeframe=tf, ticket=ticket, direction=direction, entry=result.price,
                                 stop_loss=stop, take_profit=target, volume=result.volume, planned_risk=risk,
                                 magic=request['magic'], exit_policy=policy if getattr(args, 'adaptive_exits', False) else 'fixed_2R')
                            known[ticket] = (path, risk)
                        except (ValueError, httpx.HTTPError) as error:
                            emit(path, 'REJECTED', timeframe=tf, reason=str(error))
            except (ValueError, httpx.HTTPError) as error:
                emit(supervisor, 'SCAN_ERROR', reason=str(error))
            finally:
                mt5.shutdown()
            time.sleep(min(args.interval, max(0, end_timestamp-time.time())))
    for strategy, path in journals.items():
        emit(path, 'CATALOG_FINISHED', strategy=strategy, positions_left_with_broker_stops=True)
    emit(supervisor, 'FINISHED')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('pluto', 'pluto3', 'pluto4'), default='pluto')
    parser.add_argument('--adaptive-exits', action='store_true')
    parser.add_argument('--guarded', action='store_true')
    parser.add_argument('--end-at', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--symbol', default='GOLD.i#')
    parser.add_argument('--risk-dollars', type=float, default=0)
    parser.add_argument('--total-risk-dollars', type=float, default=0)
    parser.add_argument('--max-spread', type=float, default=.5)
    parser.add_argument('--interval', type=float, default=30)
    parser.add_argument('--backend', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    if args.guarded and not args.adaptive_exits:
        parser.error('--guarded requires --adaptive-exits')
    if min(args.risk_dollars, args.total_risk_dollars) < 0 or min(args.interval, args.max_spread) <= 0:
        parser.error('risk caps must be nonnegative; spread and interval must be positive')
    return args


if __name__ == '__main__':
    import MetaTrader5
    run(parse_args(), MetaTrader5)
