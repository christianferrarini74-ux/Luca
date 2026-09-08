"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowUp, BrainCircuit, CircleDot, Database, Power, Sparkles } from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

type Message = { role: "Christian" | "Luca"; text: string; trace?: string };
type MemoryItem = { id: number; label: string; facts: { predicate: string; object: string }[] };
type RuntimeState = {
  status: "ready" | "error";
  adapter: string;
  memory: MemoryItem[];
  storage: { ssd_bytes: number; ssd_label: string };
  working_set: { ram_cells: number; vram_cells: number; trace: number[] };
};
type ChatPayload = { error?: string; reply: { text: string; trace?: number[] }; state: RuntimeState };

const emptyState: RuntimeState = {
  status: "error",
  adapter: "unknown",
  memory: [],
  storage: { ssd_bytes: 0, ssd_label: "0.00 MB" },
  working_set: { ram_cells: 0, vram_cells: 0, trace: [] },
};

async function loadState(): Promise<RuntimeState> {
  const response = await fetch(`${API_BASE}/api/state`);
  if (!response.ok) throw new Error("Luca API non disponibile.");
  return response.json();
}

async function greetLuca(): Promise<ChatPayload> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: "Ciao" }),
  });
  const payload = (await response.json()) as ChatPayload;
  if (!response.ok) throw new Error(payload.error || "Luca non ha potuto salutare.");
  return payload;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [state, setState] = useState<RuntimeState>(emptyState);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [stopped, setStopped] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadState()
      .then((nextState) => {
        setState(nextState);
        setLoading(false);
        return greetLuca();
      })
      .then((payload) => {
        setMessages([{ role: "Luca", text: payload.reply.text }]);
        setState(payload.state);
      })
      .catch((reason: Error) => {
        setError(reason.message);
        setLoading(false);
      });
  }, []);

  const send = async () => {
    const text = input.trim();
    if (!text || sending || stopping || stopped) return;
    setSending(true);
    setError(null);
    setMessages((current) => [...current, { role: "Christian", text }]);
    setInput("");
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const payload = (await response.json()) as ChatPayload;
      if (!response.ok) throw new Error(payload.error || "Luca non ha potuto elaborare il messaggio.");
      setMessages((current) => [
        ...current,
        {
          role: "Luca",
          text: payload.reply.text,
          trace: payload.reply.trace?.length ? payload.reply.trace.join(" → ") : undefined,
        },
      ]);
      setState(payload.state);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Errore di comunicazione con Luca.");
    } finally {
      setSending(false);
    }
  };

  const exit = async () => {
    if (stopping || stopped) return;
    setStopping(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/shutdown`, { method: "POST" });
      if (!response.ok) throw new Error("Luca non ha potuto completare l'arresto.");
      setStopped(true);
      setState((current) => ({ ...current, status: "error" }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Errore durante l'arresto di Luca.");
      setStopping(false);
    }
  };

  return <main className="min-h-screen bg-[#090b12] text-slate-100 selection:bg-cyan-300 selection:text-slate-950">
    <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_0%,rgba(38,210,194,.16),transparent_34%),radial-gradient(circle_at_86%_12%,rgba(93,113,255,.16),transparent_27%)]" />
    <div className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col px-5 py-5 lg:px-8">
      <header className="flex items-center justify-between border-b border-white/10 pb-5">
        <div className="flex items-center gap-3"><div className="grid size-11 place-items-center rounded-2xl border border-cyan-300/30 bg-cyan-300/10"><BrainCircuit className="size-6 text-cyan-200" /></div><div><h1 className="text-xl font-semibold tracking-[.18em]">LUCA</h1><p className="text-xs tracking-wide text-slate-400">Persistent Cognitive Memory</p></div></div>
        <div className="flex items-center gap-3"><div className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${state.status === "ready" ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-200" : "border-amber-300/20 bg-amber-300/10 text-amber-200"}`}><CircleDot className="size-3 fill-current" /> {loading ? "Connessione…" : stopped ? "Luca arrestato" : state.status === "ready" ? "Memoria attiva" : "Backend offline"}</div><button onClick={exit} disabled={stopping || stopped} className="flex items-center gap-2 rounded-full border border-rose-300/25 bg-rose-300/10 px-3 py-1.5 text-xs text-rose-100 transition hover:bg-rose-300/20 disabled:cursor-not-allowed disabled:opacity-50"><Power className="size-3.5" />{stopping ? "Arresto…" : "Esci"}</button></div>
      </header>
      {error && <div className="mt-4 rounded-2xl border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">{error} Avvia Luca con <code>python run_luca.py</code>.</div>}
      {stopped && <div className="mt-4 rounded-2xl border border-emerald-300/25 bg-emerald-300/10 px-4 py-3 text-sm text-emerald-100">Luca è stato arrestato correttamente. Puoi chiudere questa scheda.</div>}
      <section className="grid flex-1 gap-5 py-6 xl:grid-cols-[280px_minmax(0,1fr)_310px]">
        <aside className="order-2 rounded-3xl border border-white/10 bg-white/[.035] p-5 xl:order-1"><p className="mb-5 text-[11px] font-semibold uppercase tracking-[.18em] text-slate-500">Mappa della memoria</p><div className="space-y-4">{state.memory.map((item) => <div key={item.id} className="rounded-2xl border border-white/8 bg-black/20 p-3.5"><div className="flex items-center gap-2"><span className="size-2 rounded-full bg-cyan-300"/><span className="font-medium">{item.label}</span></div>{item.facts.map((fact) => <p key={`${item.id}-${fact.predicate}-${fact.object}`} className="mt-1 pl-4 text-xs text-slate-400">{fact.predicate} → {fact.object}</p>)}</div>)}</div><div className="mt-6 rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-4 text-xs text-cyan-100">{state.memory.length ? "Memoria nativa collegata" : "In attesa della memoria"}<p className="mt-1 text-[11px] text-slate-400">Le celle restano. Il contesto passa.</p></div></aside>
        <section className="flex min-h-[580px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#101522]/80 shadow-2xl shadow-black/30"><div className="flex items-center justify-between border-b border-white/8 px-6 py-4"><div><p className="text-sm font-medium">Conversazione reale</p><p className="text-xs text-slate-500">Sessione · Christian · adapter {state.adapter}</p></div><Sparkles className="size-5 text-cyan-200"/></div><div className="flex-1 space-y-5 overflow-y-auto p-6">{messages.length === 0 && <p className="text-sm text-slate-500">La conversazione apparirà qui quando Luca riceverà il primo messaggio.</p>}{messages.map((message, i) => (<div key={i} className={message.role === "Christian" ? "ml-auto max-w-[82%]" : "mr-auto max-w-[82%]"}><p className="mb-1 text-[11px] uppercase tracking-[.14em] text-slate-500">{message.role}</p><div className={message.role === "Christian" ? "rounded-2xl rounded-tr-sm bg-cyan-300 px-4 py-3 text-sm text-slate-950" : "rounded-2xl rounded-tl-sm border border-white/8 bg-white/[.055] px-4 py-3 text-sm"}>{message.text}</div>{message.trace && <p className="mt-2 font-mono text-[11px] text-cyan-200/70">trace: {message.trace}</p>}</div>))}{sending && <p className="text-xs text-slate-500">Luca sta elaborando…</p>}</div><div className="border-t border-white/8 p-4"><div className="flex gap-3 rounded-2xl border border-white/10 bg-black/20 p-2 pl-4 focus-within:border-cyan-300/40"><input value={input} disabled={sending || stopping || stopped || state.status !== "ready"} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => event.key === "Enter" && send()} placeholder="Scrivi o insegna a Luca…" className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-600"/><button onClick={send} disabled={sending || stopping || stopped || state.status !== "ready"} className="grid size-10 place-items-center rounded-xl bg-cyan-300 text-slate-950 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Invia"><ArrowUp className="size-5"/></button></div></div></section>
        <aside className="order-1 grid gap-5 sm:grid-cols-3 xl:order-3 xl:grid-cols-1"><StatusCard tier="SSD" description="Cervello completo" value={state.storage.ssd_label} width={state.storage.ssd_bytes ? "88%" : "0%"} /><StatusCard tier="RAM" description="Working set attivo" value={`${state.working_set.ram_cells} celle`} width={`${Math.min(state.working_set.ram_cells / 5, 100)}%`} /><StatusCard tier="VRAM" description="Focus del pensiero" value={`${state.working_set.vram_cells} celle`} width={`${Math.min(state.working_set.vram_cells / 5, 100)}%`} /><div className="rounded-3xl border border-violet-300/20 bg-violet-400/10 p-5"><Activity className="size-5 text-violet-200"/><p className="mt-3 text-sm font-medium">Pensiero tracciabile</p><p className="mt-1 text-xs leading-relaxed text-slate-400">Ogni risposta mostra il percorso restituito dal runtime.</p></div></aside>
      </section>
    </div>
  </main>;
}

function StatusCard({ tier, description, value, width }: { tier: string; description: string; value: string; width: string }) {
  return <div className="rounded-3xl border border-white/10 bg-white/[.035] p-5"><div className="flex items-center gap-2 text-slate-400"><Database className="size-4"/><span className="text-xs uppercase tracking-[.15em]">{tier}</span></div><p className="mt-6 text-xl font-medium">{value}</p><p className="mt-1 text-xs text-slate-400">{description}</p><div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400" style={{ width }} /></div></div>;
}
