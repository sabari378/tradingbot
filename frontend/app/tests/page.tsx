'use client';

import Link from 'next/link';
import {
  Activity,
  ArrowLeft,
  Ban,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Clock3,
  FlaskConical,
  Radio,
  Target,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { PageDropdown } from '../page-dropdown';

type TestEvent = {
  event: string;
  timestamp?: string;
  started_at?: string;
  timeframe?: string;
  direction?: string | null;
  reason?: string;
  risk_reward?: number;
  profit?: number;
};

type StrategyTest = {
  id: string;
  file: string;
  strategy: string;
  status: 'active' | 'completed' | 'interrupted';
  symbol?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  last_updated: string;
  configured_duration_seconds?: number | null;
  elapsed_seconds?: number | null;
  events: number;
  scans: number;
  entries: number;
  closures: number;
  rejections: number;
  wins: number;
  losses: number;
  recorded_pnl?: number | null;
  latest_event?: string | null;
  latest_reason?: string | null;
  recent_events: TestEvent[];
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '');

export default function TestsPage() {
  const [tests, setTests] = useState<StrategyTest[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    const load = () => fetch(`${apiUrl}/api/v1/strategy-tests`)
      .then((response) => {
        if (!response.ok) throw new Error('test results unavailable');
        return response.json();
      })
      .then((data: StrategyTest[]) => { setTests(data); setError(false); })
      .catch(() => setError(true));
    load();
    const timer = window.setInterval(load, 15000);
    return () => window.clearInterval(timer);
  }, []);

  const totals = useMemo(() => ({
    active: tests.filter((test) => test.status === 'active').length,
    entries: tests.reduce((sum, test) => sum + test.entries, 0),
    rejections: tests.reduce((sum, test) => sum + test.rejections, 0),
    completed: tests.filter((test) => test.status === 'completed').length,
  }), [tests]);

  return <main className="history-page min-h-screen">
    <nav className="flex items-center justify-between border-b border-[var(--line)] px-6 py-5 lg:px-12">
      <Link href="/" className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--mint)] text-[var(--ink)]"><Radio size={20} /></div><span className="text-xl font-semibold tracking-tight">NIRV</span></Link>
      <div className="flex items-center gap-3"><PageDropdown /><span className="hidden rounded-full border border-[var(--mint)]/30 px-3 py-1.5 text-xs text-[var(--mint)] sm:inline-flex">TEST LAB</span></div>
    </nav>
    <div className="mx-auto max-w-7xl px-6 py-8 lg:px-12">
      <header className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div><Link href="/" className="mono mb-4 flex items-center gap-2 text-xs text-[var(--muted)] hover:text-[var(--mint)]"><ArrowLeft size={14} /> DASHBOARD</Link><p className="mono mb-3 text-xs uppercase tracking-[.25em] text-[var(--mint)]">Strategy research / all runs</p><h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Test results</h1><p className="mt-3 max-w-2xl text-sm text-[var(--muted)]">Every strategy journal is kept as a separate test case, including incomplete runs and rejected setups. Results refresh without changing the recorded evidence.</p></div>
        <div className="mono flex items-center gap-2 text-xs text-[var(--muted)]"><Clock3 size={15} /> AUTO-REFRESH 15S</div>
      </header>
      {error && <div className="mb-5 flex items-center gap-2 rounded-xl border border-red-300/30 bg-red-300/5 p-4 text-sm text-red-200"><CircleAlert size={17} /> Test results API unavailable</div>}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric icon={<FlaskConical size={17} />} label="TEST RUNS" value={String(tests.length)} note={`${totals.active} active now`} />
        <Metric icon={<Target size={17} />} label="ENTRIES" value={String(totals.entries)} note="Recorded strategy fills" />
        <Metric icon={<Ban size={17} />} label="REJECTIONS" value={String(totals.rejections)} note="Risk filters applied" />
        <Metric icon={<CheckCircle2 size={17} />} label="COMPLETED" value={String(totals.completed)} note="Normal finish recorded" />
      </section>
      <section className="mt-7 space-y-4">
        {tests.map((test) => <TestCard key={test.id} test={test} />)}
        {!error && tests.length === 0 && <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-10 text-center text-sm text-[var(--muted)]">No strategy tests have been recorded.</div>}
      </section>
    </div>
  </main>;
}

function TestCard({ test }: { test: StrategyTest }) {
  const progress = test.configured_duration_seconds && test.elapsed_seconds != null
    ? Math.min(100, (test.elapsed_seconds / test.configured_duration_seconds) * 100)
    : null;
  const statusStyle = test.status === 'active' ? 'border-emerald-300/30 bg-emerald-300/10 text-emerald-200' : test.status === 'completed' ? 'border-sky-300/30 bg-sky-300/10 text-sky-200' : 'border-amber-300/30 bg-amber-300/10 text-amber-200';
  return <article className="overflow-hidden rounded-xl border border-[var(--line)] bg-[var(--panel)]">
    <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-start lg:justify-between">
      <div className="min-w-0"><div className="flex flex-wrap items-center gap-3"><h2 className="text-xl font-semibold">{test.strategy}</h2><span className={`mono rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-[.16em] ${statusStyle}`}>{test.status}</span></div><p className="mono mt-2 truncate text-[10px] text-[var(--muted)]">{test.file}</p><div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-[var(--muted)]"><span>{test.symbol ?? 'Unknown symbol'}</span><span>Started {formatDate(test.started_at)}</span><span>Updated {formatDate(test.last_updated)}</span></div></div>
      <div className="grid grid-cols-3 gap-5 lg:min-w-[360px]"><MiniStat label="SCANS" value={test.scans} /><MiniStat label="TRADES" value={test.entries} /><MiniStat label="REJECTED" value={test.rejections} /></div>
    </div>
    {progress != null && <div className="px-5 pb-5"><div className="mb-2 flex justify-between text-[10px] text-[var(--muted)]"><span className="mono">{formatDuration(test.elapsed_seconds)} ELAPSED</span><span className="mono">{progress.toFixed(0)}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-white/5"><div className="h-full rounded-full bg-[var(--mint)] transition-all" style={{ width: `${progress}%` }} /></div></div>}
    <details className="border-t border-[var(--line)]"><summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm text-[var(--muted)] hover:text-white"><span className="flex items-center gap-2"><Activity size={15} /> Latest evidence: <strong className="font-medium text-white">{test.latest_event ?? 'No events'}</strong></span><ChevronDown size={16} /></summary><div className="divide-y divide-[var(--line)] border-t border-[var(--line)]">{test.recent_events.slice().reverse().map((event, index) => <EventRow key={`${event.event}-${event.timestamp}-${index}`} event={event} />)}</div></details>
  </article>;
}

function EventRow({ event }: { event: TestEvent }) {
  const detail = event.reason ?? [event.timeframe, event.direction, event.risk_reward != null ? `${event.risk_reward.toFixed(2)}R` : null].filter(Boolean).join(' / ');
  return <div className="flex flex-col gap-2 px-5 py-3 text-xs sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><span className="h-1.5 w-1.5 rounded-full bg-[var(--mint)]" /><span className="mono text-[var(--mint)]">{event.event}</span><span className="text-[var(--muted)]">{detail}</span></div><time className="mono text-[10px] text-[var(--muted)]">{formatDate(event.timestamp ?? event.started_at)}</time></div>;
}

function Metric({ icon, label, value, note }: { icon: React.ReactNode; label: string; value: string; note: string }) { return <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><div className="flex items-center justify-between text-[var(--muted)]"><span className="mono text-[10px] tracking-[.18em]">{label}</span>{icon}</div><p className="mt-4 text-2xl font-semibold">{value}</p><p className="mt-2 text-xs text-[var(--muted)]">{note}</p></div>; }
function MiniStat({ label, value }: { label: string; value: number }) { return <div><p className="mono text-[9px] tracking-[.16em] text-[var(--muted)]">{label}</p><p className="mt-1 text-xl font-semibold">{value}</p></div>; }
function formatDate(value?: string | null) { return value ? new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '--'; }
function formatDuration(seconds?: number | null) { if (seconds == null) return '--'; const hours = Math.floor(seconds / 3600); const minutes = Math.floor((seconds % 3600) / 60); return `${hours}h ${minutes}m`; }
