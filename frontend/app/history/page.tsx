'use client';

import Link from 'next/link';
import { Activity, ArrowLeft, CircleAlert, Clock3, FileClock, Radio, Target } from 'lucide-react';
import { useEffect, useState } from 'react';

type HistoryEvent = {
  event: string;
  timestamp?: string;
  started_at?: string;
  symbol?: string;
  bid?: number;
  ask?: number;
  direction?: string | null;
  score?: number;
  confluences?: string[];
  volume_confirmed?: boolean;
  entry?: number | null;
  exit?: number;
  stop_loss?: number | null;
  take_profit?: number | null;
  pnl_points?: number;
  reason?: string;
  position_open?: boolean;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

export default function HistoryPage() {
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    const load = () => fetch(`${apiUrl}/api/v1/paper-history?limit=500`).then((response) => {
      if (!response.ok) throw new Error('history unavailable');
      return response.json();
    }).then(setEvents).catch(() => setError(true));
    load();
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const scans = events.filter((event) => event.event === 'SCAN');
  const opened = events.filter((event) => event.event === 'PAPER_OPENED');
  const closed = events.filter((event) => event.event === 'PAPER_CLOSED');
  const pnl = closed.reduce((total, event) => total + (event.pnl_points ?? 0), 0);
  const session = events.find((event) => event.event === 'SESSION_STARTED');

  return <main className="min-h-screen bg-[radial-gradient(circle_at_80%_0%,#173a3a_0%,transparent_38%),#091116]">
    <nav className="flex items-center justify-between border-b border-[var(--line)] px-6 py-5 lg:px-12"><Link href="/" className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--mint)] text-[var(--ink)]"><Radio size={20} /></div><span className="text-xl font-semibold tracking-tight">NIRV</span></Link><span className="rounded-full border border-amber-300/30 px-3 py-1.5 text-xs text-[var(--amber)]">PAPER HISTORY</span></nav>
    <div className="mx-auto max-w-7xl px-6 py-8 lg:px-12"><header className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><Link href="/" className="mono mb-4 flex items-center gap-2 text-xs text-[var(--muted)] hover:text-[var(--mint)]"><ArrowLeft size={14} /> DASHBOARD</Link><p className="mono mb-3 text-xs uppercase tracking-[.25em] text-[var(--mint)]">Experiment log / BTCUSD#</p><h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Paper trading history</h1><p className="mt-3 max-w-2xl text-sm text-[var(--muted)]">Live MT5 market data, deterministic strategy scans, and simulated outcomes. No broker orders are sent from this session.</p></div><div className="mono flex items-center gap-2 text-xs text-[var(--muted)]"><Clock3 size={15} /> AUTO-REFRESH 15S</div></header>
      {error && <div className="mb-4 flex items-center gap-2 border border-red-300/30 bg-red-300/5 p-4 text-sm text-red-200"><CircleAlert size={17} /> History API unavailable</div>}
      <section className="grid gap-4 md:grid-cols-4"><Metric icon={<FileClock size={17} />} label="SCANS" value={String(scans.length)} note={session?.started_at ? `Started ${formatTime(session.started_at)}` : 'Waiting for session'} /><Metric icon={<Target size={17} />} label="PAPER ENTRIES" value={String(opened.length)} note="Simulated fills" /><Metric icon={<Radio size={17} />} label="CLOSED TRADES" value={String(closed.length)} note="Strategy exits" /><Metric icon={<ActivityIcon />} label="P&L POINTS" value={pnl.toFixed(2)} note="Paper result" /></section>
      <section className="mt-6 overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)]"><div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4"><div><h2 className="text-lg">Scan timeline</h2><p className="mt-1 text-xs text-[var(--muted)]">Newest events appear first</p></div><span className="mono text-xs text-[var(--muted)]">{events.length} EVENTS</span></div><div className="divide-y divide-[var(--line)]">{events.slice().reverse().slice(0, 40).map((event, index) => <EventRow key={`${event.event}-${event.timestamp ?? event.started_at}-${index}`} event={event} />)}{events.length === 0 && <div className="p-8 text-center text-sm text-[var(--muted)]">No paper history recorded yet.</div>}</div></section>
    </div>
  </main>;
}

function Metric({ icon, label, value, note }: { icon: React.ReactNode; label: string; value: string; note: string }) { return <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><div className="flex items-center justify-between text-[var(--muted)]"><span className="mono text-[10px] tracking-[.18em]">{label}</span>{icon}</div><p className="mt-4 text-2xl font-semibold">{value}</p><p className="mt-2 text-xs text-[var(--muted)]">{note}</p></div>; }

function EventRow({ event }: { event: HistoryEvent }) { const isTrade = event.event.startsWith('PAPER_'); const time = event.timestamp ?? event.started_at; return <div className="flex flex-col gap-3 px-5 py-4 md:flex-row md:items-center md:justify-between"><div className="flex items-start gap-3"><span className={`mt-1 h-2 w-2 rounded-full ${isTrade ? 'bg-[var(--amber)]' : 'bg-[var(--mint)]'}`} /><div><div className="flex flex-wrap items-center gap-3"><span className="mono text-xs text-[var(--mint)]">{event.event}</span>{event.direction && <span className="mono text-xs text-[var(--amber)]">{event.direction}</span>}</div><p className="mt-1 text-sm text-[var(--muted)]">{event.event === 'SCAN' ? `${event.bid?.toFixed(2)} / ${event.ask?.toFixed(2)} · score ${event.score ?? 0} · volume ${event.volume_confirmed ? 'confirmed' : 'quiet'}` : event.event === 'PAPER_CLOSED' ? `${event.reason} · ${event.pnl_points?.toFixed(2)} points` : event.event === 'PAPER_OPENED' ? `Entry ${event.entry?.toFixed(2)} · SL ${event.stop_loss?.toFixed(2)} · TP ${event.take_profit?.toFixed(2)}` : event.symbol ?? 'Paper session'}</p></div></div><time className="mono text-xs text-[var(--muted)]">{formatTime(time)}</time></div>; }

function formatTime(value?: string) { return value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '--'; }
function ActivityIcon() { return <Activity size={17} />; }