'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, ArrowLeft, RefreshCw, SlidersHorizontal } from 'lucide-react';
import { PageDropdown } from '../page-dropdown';

type Strategy = { id: string; name: string; description: string; enabled: boolean };
type Trade = { ticket: string; session: string; strategy: string; timeframe: string; direction: string; volume: number; entry: number; sl: number; tp: number; opened_at: string; status: string; realized: number | null; floating: number | null; exit?: number; exit_reason?: string; reasons: string[] };
type Data = { strategies: Strategy[]; trades: Trade[]; sessions: { id: string; name: string }[]; live: boolean; warning?: string; checked_at: string };
const api = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '');
const money = (n: number | null) => n == null ? '—' : `${n < 0 ? '-' : n > 0 ? '+' : ''}$${Math.abs(n).toFixed(2)}`;
const pnlClass = (n: number | null) => n == null ? 'text-[var(--muted)]' : n < 0 ? 'text-red-300' : n > 0 ? 'text-[var(--mint)]' : '';

export default function StrategyPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [key, setKey] = useState('');
  const [busy, setBusy] = useState('');
  const [session, setSession] = useState('all');
  const [strategy, setStrategy] = useState('all');
  const [timeframe, setTimeframe] = useState('all');
  const [status, setStatus] = useState('all');
  const [page, setPage] = useState(0);
  const load = useCallback(async () => {
    try {
      const r = await fetch(`${api}/api/v1/strategies`, { cache: 'no-store' });
      if (!r.ok) throw new Error('Strategy service unavailable. Retrying automatically.');
      setData(await r.json()); setError('');
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to load strategies'); }
  }, []);
  useEffect(() => { load(); const timer = setInterval(load, 15000); return () => clearInterval(timer); }, [load]);
  useEffect(() => { setPage(0); }, [session, strategy, timeframe, status]);
  async function toggle(s: Strategy) {
    if (!key) { setNotice('Enter your operator API key below to change trading permissions.'); return; }
    setBusy(s.id); setNotice('');
    try {
      const r = await fetch(`${api}/api/v1/strategies/${s.id}/enabled`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': key }, body: JSON.stringify({ enabled: !s.enabled }) });
      if (!r.ok) throw new Error(r.status === 401 ? 'Invalid operator key. No change was made.' : 'Could not save trading permission.');
      setData(current => current && ({ ...current, strategies: current.strategies.map(x => x.id === s.id ? { ...x, enabled: !s.enabled } : x) }));
      setNotice(`${s.name}: new entries ${s.enabled ? 'disabled' : 'enabled'}. Existing positions keep their SL/TP. Enabling does not start a stopped session.`);
    } catch (e) { setNotice(e instanceof Error ? e.message : 'Unable to save'); }
    finally { setBusy(''); }
  }
  const scoped = useMemo(() => (data?.trades ?? []).filter(t => (session === 'all' || t.session === session) && (timeframe === 'all' || t.timeframe === timeframe)), [data, session, timeframe]);
  const filtered = scoped.filter(t => (strategy === 'all' || t.strategy === strategy) && (status === 'all' || t.status === status));
  const closed = scoped.filter(t => t.status === 'CLOSED');
  const realized = scoped.reduce((sum, t) => sum + (t.realized ?? 0), 0);
  const floating = scoped.reduce((sum, t) => sum + (t.floating ?? 0), 0);
  const pages = Math.max(1, Math.ceil(filtered.length / 20));
  const currentPage = Math.min(page, pages - 1);
  const selectClass = 'rounded-lg border border-[var(--line)] bg-[var(--panel)] px-3 py-2 text-sm max-w-full';
  return <main className="history-page min-h-screen">
    <nav className="flex items-center justify-between border-b border-[var(--line)] px-5 py-5 lg:px-12"><Link href="/" className="text-xl font-semibold">NIRV <span className="text-[var(--mint)]">/</span></Link><PageDropdown /></nav>
    <div className="mx-auto max-w-7xl px-5 py-8 lg:px-12">
      <Link href="/" className="mb-5 inline-flex items-center gap-2 text-xs text-[var(--muted)]"><ArrowLeft size={14} /> DASHBOARD</Link>
      <header className="mb-7 flex flex-wrap items-end justify-between gap-4"><div><p className="mono mb-2 text-xs uppercase tracking-[.2em] text-[var(--mint)]">Pluto / Strategy library</p><h1 className="text-4xl font-semibold">Strategy</h1><p className="mt-3 max-w-2xl text-sm text-[var(--muted)]">Compare all ten trading rules, review every entry, and choose which strategies may open new trades.</p></div><button onClick={load} className="flex items-center gap-2 rounded-lg border border-[var(--line)] px-3 py-2 text-sm"><RefreshCw size={14} /> Refresh</button></header>
      <div aria-live="polite">{error && <p className="mb-4 rounded-lg bg-red-400/10 p-3 text-red-200">{error}</p>}{data?.warning && <p className="mb-4 rounded-lg bg-amber-400/10 p-3 text-amber-200">{data.warning}. Recorded figures may be stale.</p>}</div>
      {!data && !error && <p className="p-8 text-[var(--muted)]">Loading strategy performance…</p>}
      {data && <>
        <div className="mb-5 flex flex-wrap items-center gap-3"><label className="text-sm">Session <select aria-label="Session" className={selectClass + ' ml-2'} value={session} onChange={e => setSession(e.target.value)}><option value="all">All Pluto sessions</option>{data.sessions.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label><label className="text-sm">Timeframe <select aria-label="Timeframe" className={selectClass + ' ml-2'} value={timeframe} onChange={e => setTimeframe(e.target.value)}><option value="all">All timeframes</option>{['M15','M30','H1'].map(tf => <option key={tf}>{tf}</option>)}</select></label></div>
        <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[['Total entries', String(scoped.length)], ['Open positions', String(scoped.filter(t => t.status === 'OPEN').length)], ['Realized P&L', money(realized)], ['Floating P&L', money(floating)]].map(([label, value]) => <div key={label} className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><p className="text-xs text-[var(--muted)]">{label}</p><p className="mt-2 text-2xl font-semibold">{value}</p></div>)}</section>
        <p className="my-3 text-xs text-[var(--muted)]">{data.live ? 'Broker reconciled' : 'Recorded results'} · Checked {new Date(data.checked_at).toLocaleString()} · Refreshes every 15 seconds · {closed.length} closed trades. Includes all logged trades, including positions excluded from the frozen Pluto baseline.</p>
        <section className="my-6 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-4"><div className="flex items-center gap-2"><SlidersHorizontal size={17} /><h2 className="font-semibold">Trading permissions</h2></div><p className="mt-2 text-sm text-[var(--muted)]">Toggles apply to new entries across all Pluto sessions. Turning a strategy off leaves its existing positions and SL/TP intact. These controls do not start or extend a session.</p><label className="mt-3 flex flex-wrap items-center gap-3 text-sm">Operator API key<input type="password" autoComplete="off" value={key} onChange={e => setKey(e.target.value)} placeholder="Required to change permissions" className="min-w-0 rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 sm:w-80" /></label><p className="mt-1 text-xs text-[var(--muted)]">Held only in this page’s memory.</p>{notice && <p role="status" className="mt-3 text-sm text-[var(--mint)]">{notice}</p>}</section>
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{data.strategies.map(s => {
          const own = scoped.filter(t => t.strategy === s.id); const done = own.filter(t => t.status === 'CLOSED'); const wins = done.filter(t => (t.realized ?? 0) > 0).length; const pnl = own.reduce((n,t) => n+(t.realized??0),0); const openPnl=own.reduce((n,t)=>n+(t.floating??0),0);
          return <article key={s.id} className="flex flex-col rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{s.name}</h2><button type="button" role="switch" aria-checked={s.enabled} aria-label={`Allow new ${s.name} trades`} disabled={!!busy} onClick={() => toggle(s)} className={`relative h-7 w-12 shrink-0 rounded-full transition disabled:opacity-40 ${s.enabled ? 'bg-[var(--mint)]' : 'bg-slate-600'}`}><span className={`absolute top-1 h-5 w-5 rounded-full bg-slate-950 transition-all ${s.enabled ? 'left-6' : 'left-1'}`} /></button></div><p className="mt-2 text-xs text-[var(--mint)]">New entries {s.enabled ? 'enabled' : 'disabled'}</p><p className="mt-3 flex-1 text-sm text-[var(--muted)]">{s.description}</p><dl className="mt-5 grid grid-cols-3 gap-2 text-sm"><div><dt className="text-xs text-[var(--muted)]">Trades</dt><dd className="mt-1">{own.length}</dd></div><div><dt className="text-xs text-[var(--muted)]">Open</dt><dd className="mt-1">{own.filter(t=>t.status==='OPEN').length}</dd></div><div><dt className="text-xs text-[var(--muted)]">Win rate</dt><dd className="mt-1">{done.length ? `${(100*wins/done.length).toFixed(1)}%` : '—'}</dd></div></dl><div className="mt-4 flex justify-between border-t border-[var(--line)] pt-3 text-sm"><span>Realized <b className={pnlClass(pnl)}>{money(pnl)}</b></span><span>Open <b className={pnlClass(openPnl)}>{money(openPnl)}</b></span></div><a href="#trade-history" onClick={()=>{setStrategy(s.id);setStatus('all');}} className="mt-4 text-sm text-[var(--mint)]">View trade history ?</a></article>;
        })}</section>
        <section id="trade-history" className="mt-10 scroll-mt-5"><div className="mb-4 flex flex-wrap items-center justify-between gap-3"><h2 className="flex items-center gap-2 text-xl font-semibold"><Activity size={19}/> Trade history</h2><div className="flex flex-wrap gap-2"><select aria-label="History strategy" className={selectClass} value={strategy} onChange={e=>setStrategy(e.target.value)}><option value="all">All strategies</option>{data.strategies.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><select aria-label="Trade status" className={selectClass} value={status} onChange={e=>setStatus(e.target.value)}><option value="all">All statuses</option>{['OPEN','CLOSED','UNRESOLVED'].map(s=><option key={s}>{s}</option>)}</select></div></div><p className="mb-3 text-xs text-[var(--muted)]">History filters only change this view. Win rates use closed trades; unreconciled trades are excluded.</p><div className="overflow-x-auto rounded-xl border border-[var(--line)]"><table className="w-full whitespace-nowrap text-left text-sm"><thead className="bg-[var(--panel)] text-xs text-[var(--muted)]"><tr>{['Time / ticket','Strategy / rule','TF','Side / lots','Entry','SL / TP','Status / exit','Realized','Floating'].map(h=><th key={h} className="p-3 font-medium">{h}</th>)}</tr></thead><tbody>{filtered.slice(currentPage*20,currentPage*20+20).map(t=><tr key={t.ticket} className="border-t border-[var(--line)]"><td className="p-3"><div>{new Date(t.opened_at).toLocaleString()}</div><div className="text-xs text-[var(--muted)]">#{t.ticket}</div></td><td className="p-3"><div>{data.strategies.find(s=>s.id===t.strategy)?.name}</div><div className="max-w-64 truncate text-xs text-[var(--muted)]" title={t.reasons.join(', ')}>{t.reasons.join(', ')}</div></td><td className="p-3">{t.timeframe}</td><td className="p-3">{t.direction} / {t.volume}</td><td className="p-3">{t.entry.toFixed(2)}</td><td className="p-3">{t.sl.toFixed(2)} / {t.tp.toFixed(2)}</td><td className="p-3">{t.status}{t.exit_reason ? ` / ${t.exit_reason}` : ''}</td><td className={`p-3 ${pnlClass(t.realized)}`}>{money(t.realized)}</td><td className={`p-3 ${pnlClass(t.floating)}`}>{money(t.floating)}</td></tr>)}</tbody></table>{!filtered.length && <p className="p-8 text-center text-[var(--muted)]">No trades match these filters.</p>}</div><div className="mt-3 flex items-center justify-between text-sm"><button disabled={currentPage===0} onClick={()=>setPage(currentPage-1)} className="rounded border border-[var(--line)] px-3 py-2 disabled:opacity-40">Previous</button><span>{filtered.length} trades · Page {currentPage+1} of {pages}</span><button disabled={currentPage>=pages-1} onClick={()=>setPage(currentPage+1)} className="rounded border border-[var(--line)] px-3 py-2 disabled:opacity-40">Next</button></div></section>
      </>}
    </div>
  </main>;
}
