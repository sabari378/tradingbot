"use client";

import Image from "next/image";
import { Activity, AlertOctagon, Bot, CircleStop, Crosshair, KeyRound, Mic, Play, Radio, Send, Sparkles, Wifi } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { PageDropdown } from "./page-dropdown";

type Agent = { name: string; display_name: string; status: string; activity: string; color: string };
type ControlState = { active: boolean; reason: string | null };
type SpeechRecognitionApi = { onstart: () => void; onend: () => void; onerror: () => void; onresult: (event: { results: { [key: number]: { [key: number]: { transcript: string } } } }) => void; start: () => void };

const voiceProfiles: Record<string, { index: number; pitch: number; rate: number }> = {
  nirv: { index: 4, pitch: 1.12, rate: 0.86 },
  chart: { index: 1, pitch: 1.05, rate: 0.96 },
  liquidity: { index: 2, pitch: 1.15, rate: 0.9 },
  volume: { index: 3, pitch: 0.85, rate: 1.02 },
  news: { index: 4, pitch: 1.2, rate: 0.88 },
  signal: { index: 5, pitch: 1, rate: 1.05 },
  risk: { index: 6, pitch: 0.75, rate: 0.9 },
  backtest: { index: 7, pitch: 0.9, rate: 0.92 },
  execution: { index: 8, pitch: 0.95, rate: 1.08 },
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");
const fallbackAgents: Agent[] = [
  { name: "chart", display_name: "Orion", status: "ONLINE", activity: "Reads candles and market structure", color: "cyan" },
  { name: "liquidity", display_name: "Ripple", status: "ONLINE", activity: "Finds liquidity pools and sweeps", color: "amber" },
  { name: "volume", display_name: "Pulse", status: "ONLINE", activity: "Measures participation and volume", color: "violet" },
  { name: "news", display_name: "Beacon", status: "STANDBY", activity: "Guards trades around market news", color: "red" },
  { name: "signal", display_name: "Atlas", status: "ONLINE", activity: "Combines evidence into a setup", color: "blue" },
  { name: "risk", display_name: "Sentinel", status: "ONLINE", activity: "Enforces risk and exposure limits", color: "green" },
  { name: "backtest", display_name: "Chronos", status: "ONLINE", activity: "Replays XM history without future data", color: "teal" },
  { name: "execution", display_name: "Forge", status: "STANDBY", activity: "Sends approved demo orders", color: "orange" },
];

function botUtterance(text: string, target: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return null;
  const profile = voiceProfiles[target] ?? voiceProfiles.nirv;
  const utterance = new SpeechSynthesisUtterance(text);
  const voices = window.speechSynthesis.getVoices().filter((voice) => voice.lang.toLowerCase().startsWith("en"));
  if (voices.length) utterance.voice = voices[profile.index % voices.length];
  utterance.pitch = profile.pitch;
  utterance.rate = profile.rate;
  return utterance;
}

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>(fallbackAgents);
  const [operatorKey, setOperatorKey] = useState("");
  const [command, setCommand] = useState("");
  const [response, setResponse] = useState("Nirv is watching the market.");
  const [emergencyStop, setEmergencyStop] = useState<ControlState>({ active: false, reason: null });
  const [streamLive, setStreamLive] = useState(false);
  const [voiceTarget, setVoiceTarget] = useState("nirv");
  const [listening, setListening] = useState(false);
  const [speakingTarget, setSpeakingTarget] = useState<string | null>(null);
  const speechRequest = useRef(0);

  useEffect(() => {
    fetch(`${apiUrl}/api/v1/agents`).then((r) => r.json()).then((data: Agent[]) => setAgents(data.filter((agent) => agent.name !== "master"))).catch(() => undefined);
    fetch(`${apiUrl}/api/v1/controls/emergency-stop`).then((r) => r.json()).then(setEmergencyStop).catch(() => undefined);
    const socketBase = apiUrl || `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;
    const socket = new WebSocket(socketBase.replace("http", "ws") + "/api/v1/agents/stream");
    socket.onopen = () => setStreamLive(true);
    socket.onclose = () => setStreamLive(false);
    return () => socket.close();
  }, []);

  const sendCommand = async (text: string, target = voiceTarget, requestId?: number) => {
    if (!text.trim()) return;
    setResponse("Nirv is routing the command...");
    try {
      const result = await fetch(`${apiUrl}/api/v1/voice/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(operatorKey ? { "X-API-Key": operatorKey } : {}) },
        body: JSON.stringify({ text, target }),
      });
      const body = await result.json();
      if (!result.ok) throw new Error(body.detail ?? "Command rejected");
      setResponse(body.response ?? body.message ?? "Command accepted.");
      if (requestId !== undefined && requestId !== speechRequest.current) return;
      const utterance = botUtterance(body.response ?? body.message ?? "Command accepted.", target);
      if (utterance) {
        utterance.onstart = () => setSpeakingTarget(target);
        utterance.onend = () => setSpeakingTarget(null);
        utterance.onerror = () => setSpeakingTarget(null);
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      setResponse(error instanceof Error ? error.message : "Command unavailable.");
    }
  };

  const askBot = (target: string) => {
    if (speakingTarget === target) {
      speechRequest.current += 1;
      window.speechSynthesis.cancel();
      setSpeakingTarget(null);
      const name = target === "nirv" ? "Nirv" : agents.find((agent) => agent.name === target)?.display_name;
      setResponse(`${name} stopped speaking.`);
      return;
    }
    speechRequest.current += 1;
    const requestId = speechRequest.current;
    window.speechSynthesis.cancel();
    setSpeakingTarget(null);
    setVoiceTarget(target);
    void sendCommand("What can you do?", target, requestId);
  };

  const listen = (target = voiceTarget) => {
    setVoiceTarget(target);
    const SpeechRecognition = (window as Window & { SpeechRecognition?: new () => SpeechRecognitionApi }).SpeechRecognition;
    if (!SpeechRecognition) { setResponse("Voice input is not supported in this browser."); return; }
    const recognition = new SpeechRecognition();
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => { setListening(false); setResponse("Voice input was unavailable."); };
    recognition.onresult = (event) => { void sendCommand(event.results[0][0].transcript, target); };
    recognition.start();
  };

  const setStop = async (active: boolean) => {
    const result = await fetch(`${apiUrl}/api/v1/controls/emergency-stop`, {
      method: active ? "POST" : "DELETE",
      headers: { "Content-Type": "application/json", "X-API-Key": operatorKey },
      body: active ? JSON.stringify({ reason: "operator emergency stop" }) : undefined,
    });
    if (!result.ok) { setResponse("Authentication required."); return; }
    setEmergencyStop(await result.json());
    setResponse(active ? "Execution stopped." : "Execution controls restored.");
  };

  return (
    <main className="nirv-room">
      <div className="room-wash" aria-hidden="true" />
      <nav className="room-nav">
        <div className="brand"><span className="brand-mark"><Bot size={21} /></span><strong>NIRV</strong><span className="eyebrow">COMMAND DECK / 01</span></div>
        <div className="nav-actions"><PageDropdown /><span className="link-state"><Wifi size={14} /> {streamLive ? "LIVE LINK" : "LOCAL LINK"}</span><span className="mode-pill">DEMO MODE</span></div>
      </nav>
      <header className="room-heading"><p className="eyebrow">OPERATOR INTERFACE / LIVE INTELLIGENCE</p><h1>Nirv <span>Intelligence</span></h1><p className="heading-note">One decision center. Every market signal in orbit.</p></header>
      <section className="bot-stage" aria-label="Nirv bot intelligence map">
        <div className="orbit orbit-one" /><div className="orbit orbit-two" />
        {agents.map((agent, index) => <AgentNode key={agent.name} agent={agent} index={index} count={agents.length} speaking={speakingTarget === agent.name} onActivate={() => askBot(agent.name)} />)}
        <button className={`nirv-core ${speakingTarget === "nirv" ? "is-speaking" : ""}`} onClick={() => askBot("nirv")} aria-label={speakingTarget === "nirv" ? "Stop Nirv speaking" : "Ask Nirv what it can do"}><span className="core-pulse" /><span className="nirv-avatar"><Image src="/images/nirv-bot-avatar.jpg" alt="Nirv bot" fill sizes="150px" priority /></span><span className="nirv-core-label"><strong>NIRV</strong><span className="core-status"><i /> {emergencyStop.active ? "STOPPED" : speakingTarget === "nirv" ? "SPEAKING" : "ONLINE"}</span></span></button>
        <button className={`nirv-mic ${listening && voiceTarget === "nirv" ? "is-listening" : ""}`} onClick={() => listen("nirv")} aria-label="Speak to Nirv"><Mic size={17} /><span>{listening && voiceTarget === "nirv" ? "LISTENING" : "TALK TO NIRV"}</span></button>
      </section>
      <details className="quick-controls">
        <summary><span><Sparkles size={14} /> TALK TO {voiceTarget === "nirv" ? "NIRV" : agents.find((agent) => agent.name === voiceTarget)?.display_name?.toUpperCase()}</span><small>TYPE OR CONTROL</small></summary>
        <div className="quick-command"><input value={command} onChange={(event) => setCommand(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { void sendCommand(command); setCommand(""); } }} placeholder="Ask a question or enter a command..." /><button onClick={() => { void sendCommand(command); setCommand(""); }} aria-label="Send command"><Send size={15} /></button><button onClick={() => listen(voiceTarget)} className={listening ? "is-listening" : ""} aria-label="Speak to selected bot"><Mic size={15} /></button></div>
        <div className="quick-actions"><label><KeyRound size={14} /><input type="password" value={operatorKey} onChange={(event) => setOperatorKey(event.target.value)} placeholder="Operator API key" /></label><button className="start-button" disabled={!operatorKey || emergencyStop.active} onClick={() => void sendCommand("start demo trading", "nirv")}><Play size={14} /> START</button><button className="stop-button" onClick={() => void setStop(!emergencyStop.active)}><CircleStop size={14} /> {emergencyStop.active ? "RESET" : "STOP"}</button></div>
      </details>
      <section className="status-strip"><div><span className="eyebrow">CURRENT SIGNAL</span><strong>{response}</strong></div><div className="status-right"><Activity size={16} /><span>MT5 / DEMO</span><span className="status-dot" /></div></section>
      <footer className="room-footer"><span><Crosshair size={14} /> TWO-STRATEGY ALIGNMENT</span><span><Sparkles size={14} /> PRICE ACTION + IMBALANCE</span><span className="footer-stop"><AlertOctagon size={14} /> EMERGENCY STOP READY</span></footer>
    </main>
  );
}

function AgentNode({ agent, index, count, speaking, onActivate }: { agent: Agent; index: number; count: number; speaking: boolean; onActivate: () => void }) {
  const angle = (index / count) * Math.PI * 2 - Math.PI / 2;
  const position = {
    left: `${50 + Math.cos(angle) * 39}%`,
    top: `${50 + Math.sin(angle) * 42}%`,
  };

  return <button className={`agent-node ${speaking ? "is-speaking" : ""}`} style={position} onClick={onActivate} aria-label={speaking ? `Stop ${agent.display_name} speaking` : `Ask ${agent.display_name} what it can do`}><span className={`node-icon node-${agent.color}`}><Radio size={16} /></span><span><strong>{agent.display_name}</strong><small>{speaking ? "Speaking — click again to stop" : agent.activity}</small></span><i className={agent.status === "ONLINE" ? "online" : "standby"} /></button>;
}
