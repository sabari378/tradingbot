"""Read-only per-strategy monitoring; never submits or modifies orders."""
import argparse
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import MetaTrader5 as mt5
from nirv.strategies.catalog import CATALOG_STRATEGIES

RULES = {
 'sma_crossover':'Fresh 20/50 SMA crossover',
 'donchian_breakout':'Close beyond the previous 20-candle range',
 'bollinger_reversion':'Fresh close outside the 2-standard-deviation band; countertrend entry',
 'rsi_countertrend':'RSI crosses back above 30 or below 70',
 'volatility_breakout':'20-candle breakout with range at least 1.5 ATR',
 'engulfing_reversal':'Current body engulfs the previous opposite-direction body',
 'market_structure':'Close beyond the latest confirmed swing; fresh crossing is not required',
 'liquidity_sweep':'Sweep of the previous 20-candle extreme followed by a close back inside',
 'fair_value_gap':'New three-candle imbalance',
 'double_top':'Two similar swing highs, bearish displacement and previous-low break',
}


def read_rows(path):
    rows=[]
    for line in path.read_text().splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue  # The writer may be appending its last line.
    return rows


def snapshot(folder):
    if not mt5.initialize(timeout=5000):
        raise RuntimeError(str(mt5.last_error()))
    try:
        account=mt5.account_info()
        positions=mt5.positions_get()
        if account is None or positions is None:
            raise RuntimeError('Account or positions unavailable')
        active={p.ticket:p for p in positions}
        trades=[]; summaries=[]
        for strategy in CATALOG_STRATEGIES:
            scans={};intents={};rows=read_rows(folder/(strategy+'-demo.jsonl'))
            for row in rows:
                if row['event']=='SCAN': scans[row['timeframe']]=row
                if row['event']=='ORDER_INTENT': intents[row['timeframe']]=row
                if row['event']!='FILLED': continue
                ticket=int(row['ticket']);tf=row['timeframe']
                trade=dict(row, strategy=strategy, rule=('Fresh crossing of the confirmed swing level' if strategy == 'market_structure' and scans.get(tf,{}).get('structure_context') else RULES[strategy]),
                           structure_context=scans.get(tf,{}).get('structure_context'),
                           signal_key=intents.get(tf,{}).get('signal_key'),
                           confluences=scans.get(tf,{}).get('confluences',[]))
                deals=mt5.history_deals_get(position=ticket)
                trade['realized']=None if deals is None else round(sum(d.profit+d.commission+d.swap+d.fee for d in deals),2)
                if ticket in active:
                    p=active[ticket]
                    trade.update(status='OPEN',floating=round(p.profit+p.swap,2),current=p.price_current,sl=p.sl,tp=p.tp)
                elif deals and any(d.entry in (mt5.DEAL_ENTRY_OUT,mt5.DEAL_ENTRY_OUT_BY) for d in deals):
                    last=deals[-1]
                    reason={mt5.DEAL_REASON_SL:'SL',mt5.DEAL_REASON_TP:'TP'}.get(last.reason,str(last.reason))
                    trade.update(status='CLOSED',floating=0,exit=last.price,exit_reason=reason)
                else:
                    trade.update(status='UNRESOLVED',floating=None)
                trades.append(trade)
            own=[t for t in trades if t['strategy']==strategy]
            closed=[t for t in own if t['status']=='CLOSED']
            summaries.append(dict(strategy=strategy,entries=len(own),open=sum(t['status']=='OPEN' for t in own),
                                  closed=len(closed),wins=sum(t['realized']>0 for t in closed),
                                  losses=sum(t['realized']<0 for t in closed),
                                  unresolved=sum(t['status']=='UNRESOLVED' for t in own),
                                  realized=round(sum(t['realized'] or 0 for t in own),2),
                                  floating=round(sum(t['floating'] or 0 for t in own),2),
                                  rejected=dict(Counter(r['reason'] for r in rows if r['event']=='REJECTED'))))
        heartbeat=read_rows(folder/'supervisor.jsonl')[-1]
        result=dict(checked_at=datetime.now().astimezone().isoformat(),balance=account.balance,equity=account.equity,
                    broker_positions=len(positions),heartbeat=heartbeat,strategies=summaries,trades=trades)
        lines=['# Demo strategy monitor', '', 'Updated: '+result['checked_at'], '',
               f'Balance: ${account.balance:.2f}; equity: ${account.equity:.2f}; broker positions: {len(positions)}.', '',
               '| Strategy | Entries | Open | Closed | Wins | Losses | Realized USD | Floating USD |',
               '|---|---:|---:|---:|---:|---:|---:|---:|']
        for s in summaries:
            lines.append('| '+ ' | '.join(str(s[k]) for k in ('strategy','entries','open','closed','wins','losses','realized','floating'))+' |')
        lines += ['', '## Individual trades', '', '| Ticket | Strategy | TF | Side | Lots | Status | Realized USD | Floating USD | Exit |',
                  '|---|---|---|---|---:|---|---:|---:|---|']
        for t in trades:
            lines.append('| '+' | '.join(str(t.get(k,'')) for k in ('ticket','strategy','timeframe','direction','volume','status','realized','floating','exit_reason'))+' |')
        if 'pluto4' in folder.name:
            lines += ['', 'Pluto 4 additions: Liquidity Sweep requires a directional close in the outer third; Engulfing requires a test of the previous 20-bar extreme. Filtered baseline signals are logged in SCAN records.']
        lines += ['', '## Entry rules', '']+[f'- **{s}:** {('Fresh crossing of the latest confirmed swing' if s == 'market_structure' and any(v in folder.name for v in ('pluto3', 'pluto4')) else RULES[s])}' for s in CATALOG_STRATEGIES]
        lines += ['', 'Each strategy/timeframe can enter once per qualifying candle, including while earlier positions remain open. Different strategies can respond to the same market move. Pluto 3/4 Market Structure requires a fresh crossing of the confirmed swing level; earlier Pluto sessions retain the original rule.',
                  '', 'Broker tickets are used for reconciliation because broker history timestamps may differ from local time. Unresolved history is not treated as a confirmed close.']
        for name,content in [('analysis-latest.json',json.dumps(result,indent=2)),('analysis-latest.md','\n'.join(lines)+'\n')]:
            temp=folder/(name+'.tmp');temp.write_text(content,encoding='utf-8');temp.replace(folder/name)
        print(json.dumps({k:result[k] for k in ('checked_at','balance','equity','broker_positions','strategies')}),flush=True)
    finally:
        mt5.shutdown()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',required=True);p.add_argument('--end-at');args=p.parse_args()
    while True:
        try: snapshot(Path(args.folder))
        except Exception as error: print(json.dumps({'monitor_error':str(error)}),flush=True)
        if not args.end_at or time.time()>=datetime.fromisoformat(args.end_at).timestamp(): break
        time.sleep(min(60,max(0,datetime.fromisoformat(args.end_at).timestamp()-time.time())))
