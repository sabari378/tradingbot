'use client';

import { useEffect, useState } from 'react';
import { Activity, ArrowDownRight, ArrowUpRight, Bot, ShieldCheck, WifiOff } from 'lucide-react';

type Agent = { name: string; display_name: string; status: string };

const fallbackAgents: Agent[] = [
  ['master', 'Nirv Master', 'ONLINE'], ['chart', 'Nirv Chart', 'ONLINE'], ['liquidity', 'Nirv Liquidity', 'ONLINE'], ['volume', 'Nirv Volume', 'ONLINE'], ['news', 'Nirv News', 'ONLINE'], ['signal', 'Nirv Signal', 'ONLINE'], ['risk', 'Nirv Risk', 'ONLINE'], ['execution', 'Nirv Execution', 'STANDBY'],
].map(([name, display_name, status]) => ({ name, display_name, status }));

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>(fallbackAgents);
  const [connected, setConnected] = useState(false);
  useEffect(() => { fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'}/api/v1/agents`).then((r) => r.json()).then(setAgents).catch(() => setConnected(false)); }, []);
  return <main className="min-h-screen bg-[radial-gradient(circle_at_80%_0%,#173a3a_0%,transparent_38%),#091116]">
    <nav className="flex items-center justify-between border-b border-[var(--line)] px-6 py-5 lg:px-12"><div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--mint)] text-[var(--ink)]"><Bot size={20} /></div><span className="text-xl font-semibold tracking-tight">NIRV</span></div><div className="flex items-center gap-3 text-xs"><span className="rounded-full border border-amber-300/30 px-3 py-1.5 text-[var(--amber)]">PAPER MODE</span><span className="mono text-[var(--muted)]">XAUUSD / M5-M15-H1</span></div></nav>
    <div className="mx-auto max-w-7xl px-6 py-8 lg:px-12"><header className="mb-10 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="mono mb-3 text-xs uppercase tracking-[.25em] text-[var(--mint)]">Decision workspace / 01</p><h1 className="text-4xl font-semibold tracking-tight md:text-6xl">Gold, observed<br /><span className="text-[var(--muted)]">without guesswork.</span></h1></div><div className="rounded-lg border border-amber-300/30 bg-amber-300/5 px-4 py-3 text-sm text-[var(--amber)]"><WifiOff className="mr-2 inline" size={16} /> MARKET DATA NOT CONNECTED</div></header>
    <section className="grid gap-4 md:grid-cols-4"><Metric label="XAUUSD PRICE" value="--" note="Provider required" /><Metric label="MARKET BIAS" value="UNKNOWN" note="No live candles" /><Metric label="AI CONFIDENCE" value="0%" note="No candidate" /><Metric label="RISK STATE" value="LOCKED" note="Awaiting data" /></section>
    <div className="mt-4 grid gap-4 lg:grid-cols-[1.35fr_.65fr]"><section className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6"><div className="mb-8 flex items-center justify-between"><div><p className="mono text-xs text-[var(--muted)]">TRADE CANDIDATE</p><h2 className="mt-2 text-2xl">No executable setup</h2></div><ShieldCheck className="text-[var(--mint)]" /></div><div className="grid grid-cols-3 gap-3">{['Entry', 'Stop Loss', 'Take Profit'].map((label) => <div key={label} className="border-l border-[var(--line)] pl-4"><p className="text-xs text-[var(--muted)]">{label}</p><p className="mono mt-2 text-lg">--</p></div>)}</div><div className="mt-8 border-t border-[var(--line)] pt-5 text-sm text-[var(--muted)]">Nirv will not propose or execute a trade until a market provider is connected, deterministic confluence is present, risk approves, and a user approves.</div></section><section className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6"><div className="mb-5 flex items-center justify-between"><h2 className="text-lg">Agent status</h2><Activity size={18} className="text-[var(--mint)]" /></div><div className="space-y-3">{agents.map((agent) => <div key={agent.name} className="flex items-center justify-between border-b border-[var(--line)] pb-3 text-sm"><span>{agent.display_name}</span><span className={agent.status === 'STANDBY' ? 'text-[var(--muted)]' : 'text-[var(--mint)]'}><span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-current" />{agent.status}</span></div>)}</div></section></div></div>
  </main>;
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) { return <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-5"><p className="mono text-[10px] tracking-[.18em] text-[var(--muted)]">{label}</p><p className="mt-4 text-2xl font-semibold">{value}</p><p className="mt-2 text-xs text-[var(--muted)]">{note}</p></div>; }
