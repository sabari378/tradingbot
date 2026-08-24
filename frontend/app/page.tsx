'use client';

import Link from 'next/link';
import { Activity, AlertOctagon, Bot, BrainCircuit, ChevronRight, History, LineChart, Mic, Radio, Send, ShieldCheck, Sparkles, Volume2, Wifi } from 'lucide-react';
import { useEffect, useState } from 'react';

type Agent = { name: string; display_name: string; status: string; activity: string; color: string };
type VoiceResult = { intent: string; response: string; requires_confirmation: boolean };
type ControlState = { active: boolean; reason: string | null };
type LiveAnalysis = { symbol: string; direction: string | null; confidence: number; market_data_connected: boolean; analyzed_at: string; snapshot: { timeframe: string; candle_count: number; bid: number; ask: number; latest_close: number; latest_volume: number }; agents: { agent: string; reasoning_summary: string; features: Record<string, unknown> }[]; rejection_reasons: string[] };
type SpeechRecognitionApi = { onstart: () => void; onend: () => void; onerror: () => void; onresult: (event: { results: { [key: number]: { [key: number]: { transcript: string } } } }) => void; start: () => void };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';
const fallbackAgents: Agent[] = [
  ['master', 'Nirv Master', 'ONLINE', 'Coordinating the decision chain', 'mint'], ['chart', 'Nirv Chart', 'ONLINE', 'Reading market structure and candles', 'cyan'], ['liquidity', 'Nirv Liquidity', 'ONLINE', 'Watching equal highs, lows, and sweeps', 'amber'], ['volume', 'Nirv Volume', 'ONLINE', 'Comparing tick volume to its baseline', 'violet'], ['news', 'Nirv News', 'STANDBY', 'No provider connected; trading remains guarded', 'red'], ['signal', 'Nirv Signal', 'ONLINE', 'Waiting for complete ICT/SMC confluence', 'blue'], ['risk', 'Nirv Risk', 'ONLINE', 'Enforcing spread, R:R, and exposure limits', 'green'], ['execution', 'Nirv Execution', 'STANDBY', 'Armed only after explicit confirmation', 'orange'],
].map(([name, display_name, status, activity, color]) => ({ name, display_name, status, activity, color }));

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>(fallbackAgents);
  const [selected, setSelected] = useState<Agent>(fallbackAgents[0]);
  const [command, setCommand] = useState('');
  const [response, setResponse] = useState('Voice link ready. Ask Nirv for status, analysis, positions, or account risk.');
  const [listening, setListening] = useState(false);
  const [emergencyStop, setEmergencyStop] = useState<ControlState>({ active: false, reason: null });
  const [operatorKey, setOperatorKey] = useState('');
  const [controlMessage, setControlMessage] = useState('');
  const [streamLive, setStreamLive] = useState(false);
  const [analysis, setAnalysis] = useState<LiveAnalysis | null>(null);

  useEffect(() => {
    fetch(`${apiUrl}/api/v1/agents`).then((r) => r.json()).then((data) => { setAgents(data); setSelected(data[0]); }).catch(() => undefined);
    fetch(`${apiUrl}/api/v1/controls/emergency-stop`).then((r) => r.json()).then(setEmergencyStop).catch(() => undefined);
    const socket = new WebSocket(apiUrl.replace('http', 'ws') + '/api/v1/agents/stream');
    socket.onopen = () => setStreamLive(true);
    socket.onclose = () => setStreamLive(false);
    return () => socket.close();
  }, []);

  const setStop = async (active: boolean) => {
    const headers = { 'Content-Type': 'application/json', 'X-API-Key': operatorKey };
    const result = await fetch(`${apiUrl}/api/v1/controls/emergency-stop`, { method: active ? 'POST' : 'DELETE', headers, body: active ? JSON.stringify({ reason: 'operator emergency stop' }) : undefined });
    if (!result.ok) { setControlMessage('Authentication required. Enter the configured operator API key.'); return; }
    setEmergencyStop(await result.json());
    setControlMessage(active ? 'Execution blocked immediately.' : 'Execution controls restored.');
  };

  const runAnalysis = async (symbol = 'BTCUSD#') => {
    setResponse('Nirv is reading 200 closed candles from MT5...');
    try {
      const result = await fetch(`${apiUrl}/api/v1/analysis/live?symbol=${encodeURIComponent(symbol)}&timeframe=M5`).then((r) => { if (!r.ok) throw new Error('analysis unavailable'); return r.json(); });
      setAnalysis(result);
      setResponse(`Analysis complete for ${result.symbol}. ${result.direction ? `${result.direction} candidate detected.` : 'No executable setup detected.'}`);
    } catch { setResponse('Live analysis unavailable. Check the backend and MT5 gateway.'); }
  };

  const sendCommand = async (text = command) => {
    if (!text.trim()) return;
    setResponse('Nirv is routing your command...');
    try {
      const result: VoiceResult = await fetch(`${apiUrl}/api/v1/voice/command`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(operatorKey ? { 'X-API-Key': operatorKey } : {}) }, body: JSON.stringify({ text }) }).then((r) => r.json());
      if (result.intent === 'ANALYZE') { await runAnalysis(text.match(/BTCUSD#?/i)?.[0] ?? 'BTCUSD#'); return; }
      setResponse(result.response + (result.requires_confirmation ? ' Say confirm only after reviewing the trade details.' : ''));
      setCommand('');
    } catch { setResponse('Voice link unavailable. Check that the backend is running.'); }
  };

  const listen = () => {
    const SpeechRecognition = (window as Window & { SpeechRecognition?: new () => SpeechRecognitionApi }).SpeechRecognition;
    if (!SpeechRecognition) { setResponse('Microphone input is not supported in this browser. Use the command field below.'); return; }
    const recognition = new SpeechRecognition();
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => { setListening(false); setResponse('Microphone input was unavailable. Use typed command input.'); };
    recognition.onresult = (event) => { const text = event.results[0][0].transcript; setCommand(text); void sendCommand(text); };
    recognition.start();
  };

  return <main className="min-h-screen bg-[radial-gradient(circle_at_75%_0%,#123b3d_0%,transparent_35%),linear-gradient(135deg,#081014_0%,#0d171c_55%,#101515_100%)]">
    <nav className="flex items-center justify-between border-b border-[var(--line)] px-6 py-5 lg:px-12"><div className="flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-lg bg-[var(--mint)] text-[var(--ink)]"><Bot size={20} /></div><span className="text-xl font-semibold tracking-tight">NIRV</span><span className="mono hidden text-[10px] text-[var(--muted)] md:inline">COMMAND DECK / 01</span></div><div className="flex items-center gap-4 text-xs"><Link href="/history" className="flex items-center gap-2 text-[var(--muted)] hover:text-[var(--mint)]"><History size={15} /> HISTORY</Link><span className="flex items-center gap-2 text-[var(--mint)]"><Wifi size={14} /> LOCAL LINK</span><span className="rounded-full border border-amber-300/30 px-3 py-1.5 text-[var(--amber)]">DEMO MODE</span></div></nav>
    <div className="mx-auto max-w-7xl px-6 py-8 lg:px-12"><header className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><p className="mono mb-3 text-xs uppercase tracking-[.25em] text-[var(--mint)]">Operator interface / live agents</p><h1 className="text-4xl font-semibold tracking-tight md:text-6xl">Nirv command deck</h1><p className="mt-3 max-w-2xl text-sm text-[var(--muted)]">One place to hear what every bot sees, ask for a decision, and keep the risk boundary visible.</p></div><div className="flex items-center gap-3 rounded-lg border border-[var(--line)] bg-black/10 px-4 py-3 text-xs text-[var(--muted)]"><Radio className={streamLive ? 'text-[var(--mint)]' : 'text-[var(--amber)]'} size={16} /> {streamLive ? 'LIVE AGENT STREAM' : 'RECONNECTING'} </div></header>
      <section className="mb-6 flex flex-col gap-3 rounded-xl border border-red-300/20 bg-red-300/5 p-4 md:flex-row md:items-center md:justify-between"><div className="flex items-center gap-3"><AlertOctagon className={emergencyStop.active ? 'text-red-300' : 'text-[var(--amber)]'} size={19} /><div><p className="mono text-[10px] tracking-[.18em] text-red-200">EMERGENCY STOP / {emergencyStop.active ? 'ACTIVE' : 'READY'}</p><p className="mt-1 text-sm text-[var(--muted)]">{emergencyStop.active ? emergencyStop.reason : 'Stops all new execution requests immediately.'}</p></div></div><div className="flex flex-wrap items-center gap-2"><input type="password" value={operatorKey} onChange={(event) => setOperatorKey(event.target.value)} placeholder="Operator API key" className="w-44 border border-[var(--line)] bg-black/20 px-3 py-2 text-xs outline-none" />{emergencyStop.active ? <button onClick={() => void setStop(false)} className="border border-[var(--mint)]/50 px-3 py-2 text-xs text-[var(--mint)]">RESET STOP</button> : <button onClick={() => void setStop(true)} className="bg-red-300 px-3 py-2 text-xs font-semibold text-[#160d0d]">STOP EXECUTION</button>}</div>{controlMessage && <span className="text-xs text-red-200">{controlMessage}</span>}</section>
      <section className="grid gap-4 lg:grid-cols-[1.15fr_.85fr]"><div className="rounded-xl border border-[var(--mint)]/30 bg-[var(--panel)] p-6 shadow-[0_0_50px_rgba(128,228,194,.05)]"><div className="flex items-start justify-between"><div><p className="mono text-xs tracking-[.18em] text-[var(--mint)]">VOICE COMMAND CONSOLE</p><h2 className="mt-3 text-2xl">Talk to the deck</h2></div><button onClick={listen} title="Activate voice input" className={`grid h-12 w-12 place-items-center rounded-full border ${listening ? 'border-[var(--amber)] bg-[var(--amber)]/15 text-[var(--amber)]' : 'border-[var(--mint)]/40 text-[var(--mint)]'} transition`}>{listening ? <Volume2 size={21} /> : <Mic size={21} />}</button></div><div className="mt-6 flex gap-2"><input value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void sendCommand(); }} placeholder="Ask: status, analyze BTCUSD, show positions..." className="min-w-0 flex-1 border border-[var(--line)] bg-black/20 px-4 py-3 text-sm outline-none placeholder:text-[var(--muted)] focus:border-[var(--mint)]" /><button onClick={() => void sendCommand()} title="Send command" className="grid w-12 place-items-center bg-[var(--mint)] text-[var(--ink)] hover:bg-white"><Send size={17} /></button></div><button onClick={() => void runAnalysis()} className="mt-4 flex items-center gap-2 border border-[var(--line)] px-3 py-2 text-xs text-[var(--mint)] hover:border-[var(--mint)]"><LineChart size={15} /> RUN LIVE BTCUSD# ANALYSIS</button><div className="mt-5 flex gap-3 border-t border-[var(--line)] pt-4 text-sm"><Sparkles className="shrink-0 text-[var(--amber)]" size={17} /><p className="text-[var(--muted)]">{response}</p></div></div><div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-lg border border-[var(--mint)]/30 text-[var(--mint)]"><BrainCircuit size={21} /></div><div><p className="mono text-[10px] text-[var(--muted)]">SELECTED INTELLIGENCE</p><h2 className="mt-1 text-xl">{selected.display_name}</h2></div></div><div className="mt-7 border-l-2 border-[var(--mint)] pl-4"><p className="text-xs uppercase tracking-wider text-[var(--muted)]">Current activity</p><p className="mt-2 text-lg">{selected.activity}</p></div><div className="mt-6 flex items-center justify-between text-xs"><span className="flex items-center gap-2 text-[var(--mint)]"><span className="h-2 w-2 rounded-full bg-current" /> {selected.status}</span><span className="mono text-[var(--muted)]">EXPLAINABLE / MONITORED</span></div></div></section>
      {analysis && <section className="mt-6 rounded-xl border border-[var(--line)] bg-[var(--panel)] p-6"><div className="flex flex-col justify-between gap-3 md:flex-row md:items-center"><div><p className="mono text-xs tracking-[.18em] text-[var(--mint)]">LIVE ANALYSIS EVIDENCE</p><h2 className="mt-2 text-2xl">{analysis.symbol} / {analysis.snapshot.timeframe}</h2></div><span className="mono text-xs text-[var(--muted)]">{analysis.snapshot.candle_count} CLOSED CANDLES · {analysis.market_data_connected ? 'MT5 CONNECTED' : 'DATA UNAVAILABLE'}</span></div><div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5"><Evidence label="BID / ASK" value={`${analysis.snapshot.bid.toFixed(2)} / ${analysis.snapshot.ask.toFixed(2)}`} /><Evidence label="LAST CLOSE" value={analysis.snapshot.latest_close.toFixed(2)} /><Evidence label="TICK VOLUME" value={String(analysis.snapshot.latest_volume)} /><Evidence label="DIRECTION" value={analysis.direction ?? 'NONE'} /><Evidence label="CONFIDENCE" value={`${Math.round(analysis.confidence * 100)}%`} /></div><div className="mt-6 grid gap-3 md:grid-cols-2"><div><p className="mono text-[10px] text-[var(--muted)]">DECISION REASONS</p><p className="mt-2 text-sm text-[var(--muted)]">{analysis.rejection_reasons.length ? analysis.rejection_reasons.join(' · ') : 'All required confluences aligned.'}</p></div><div><p className="mono text-[10px] text-[var(--muted)]">AGENT EVIDENCE</p><p className="mt-2 text-sm text-[var(--muted)]">{analysis.agents.map((agent) => `${agent.agent}: ${agent.reasoning_summary}`).join(' · ')}</p></div></div></section>}
      <div className="mb-4 mt-8 flex items-center justify-between"><div><p className="mono text-xs tracking-[.18em] text-[var(--muted)]">AGENT ARRAY</p><h2 className="mt-2 text-2xl">What the bots are doing</h2></div><span className="mono text-xs text-[var(--muted)]">CLICK A NODE FOR DETAIL</span></div><section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{agents.map((agent, index) => <button key={agent.name} onClick={() => setSelected(agent)} className={`group relative overflow-hidden rounded-xl border p-5 text-left transition ${selected.name === agent.name ? 'border-[var(--mint)] bg-[var(--mint)]/10' : 'border-[var(--line)] bg-[var(--panel)] hover:border-[var(--mint)]/50'}`}><div className="absolute right-4 top-4 text-[var(--muted)]"><ChevronRight size={16} className="transition group-hover:translate-x-1" /></div><div className={`mb-6 grid h-12 w-12 place-items-center rounded-full border ${selected.name === agent.name ? 'border-[var(--mint)] text-[var(--mint)]' : 'border-[var(--line)] text-[var(--muted)]'}`}><span className="mono text-sm">0{index + 1}</span></div><div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${agent.status === 'ONLINE' ? 'bg-[var(--mint)]' : 'bg-[var(--amber)]'}`} /><h3 className="font-medium">{agent.display_name}</h3></div><p className="mt-3 min-h-10 text-xs leading-5 text-[var(--muted)]">{agent.activity}</p><div className="mt-5 flex items-center justify-between border-t border-[var(--line)] pt-3"><span className="mono text-[10px] text-[var(--muted)]">{agent.status}</span><Activity size={14} className="text-[var(--mint)]" /></div></button>)}</section>
      <footer className="mt-8 flex flex-col justify-between gap-3 border-t border-[var(--line)] py-5 text-xs text-[var(--muted)] md:flex-row"><span className="flex items-center gap-2"><ShieldCheck size={15} className="text-[var(--mint)]" /> Every execution action remains confirmation-gated.</span><span className="mono">{new Date().toISOString().slice(0, 10)} / NIRV CONTROL SYSTEM</span></footer>
    </div>
  </main>;
}

function Evidence({ label, value }: { label: string; value: string }) { return <div className="border-l border-[var(--line)] pl-3"><p className="mono text-[10px] text-[var(--muted)]">{label}</p><p className="mt-2 text-lg">{value}</p></div>; }
