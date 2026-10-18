"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowUp, BrainCircuit, CircleDot, Cpu, Database, Layers, Power, RotateCcw, Sparkles } from "lucide-react";

const API_BASE = "http://127.0.0.1:8765";

type Message = { role: "Christian" | "Luca"; text: string; trace?: string };
type MemoryItem = { id: number; label: string; slug?: string; content?: string; facts: { predicate: string; object: string }[] };
type TierNode = {
  id: number;
  slug: string;
  title: string;
  content: string;
  expanded: boolean;
  recall_count: number;
  incoming_ids: number[];
  outgoing_ids: number[];
};
type RuntimeState = {
  status: "ready" | "error";
  adapter: string;
  memory: MemoryItem[];
  tiers?: {
    vram: { capacity: number; nodes: TierNode[]; chains: string[][] };
    ram: { capacity: number; nodes: TierNode[] };
    ssd: { total_cells: number };
  };
  storage: { ssd_bytes: number; ssd_label: string };
  working_set: { ram_cells: number; vram_cells: number; ssd_cells?: number; trace: number[] };
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

  const recallNode = async (nodeId: number) => {
    if (sending || stopping || stopped) return;
    try {
      const response = await fetch(`${API_BASE}/api/recall`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_id: nodeId }),
      });
      const payload = (await response.json()) as { state?: RuntimeState; error?: string };
      if (!response.ok || !payload.state) throw new Error(payload.error || "Impossibile richiamare il nodo.");
      setState(payload.state);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Errore durante il richiamo sinaptico.");
    }
  };

  const resetSession = async () => {
    if (sending || stopping || stopped) return;
    setSending(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
      const payload = (await response.json()) as ChatPayload;
      if (!response.ok) throw new Error(payload.error || "Impossibile azzerare la sessione.");
      setMessages([{ role: "Luca", text: payload.reply.text }]);
      setState(payload.state);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Errore durante il reset della sessione.");
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

  const vramNodes = state.tiers?.vram.nodes ?? [];
  const ramNodes = state.tiers?.ram.nodes ?? [];
  const chains = state.tiers?.vram.chains ?? [];
  const vramCap = state.tiers?.vram.capacity ?? 8;
  const ramCap = state.tiers?.ram.capacity ?? 32;

  return (
    <main className="min-h-screen bg-[#090b12] text-slate-100 selection:bg-cyan-300 selection:text-slate-950">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_0%,rgba(38,210,194,.16),transparent_34%),radial-gradient(circle_at_86%_12%,rgba(93,113,255,.16),transparent_27%)]" />
      <div className="relative mx-auto flex min-h-screen max-w-[1680px] flex-col px-5 py-5 lg:px-8">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-2xl border border-cyan-300/30 bg-cyan-300/10">
              <BrainCircuit className="size-6 text-cyan-200" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-[.18em]">LUCA</h1>
              <p className="text-xs tracking-wide text-slate-400">Giostra Sinaptica · VRAM ↔ RAM ↔ SSD</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${
                state.status === "ready"
                  ? "border-emerald-300/20 bg-emerald-300/10 text-emerald-200"
                  : "border-amber-300/20 bg-amber-300/10 text-amber-200"
              }`}
            >
              <CircleDot className="size-3 fill-current" />{" "}
              {loading ? "Connessione…" : stopped ? "Luca arrestato" : state.status === "ready" ? "Sinapsi attive" : "Backend offline"}
            </div>
            <button
              onClick={resetSession}
              disabled={sending || stopping || stopped}
              className="flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs text-cyan-100 transition hover:bg-cyan-300/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RotateCcw className="size-3.5" />
              Nuova Sessione
            </button>
            <button
              onClick={exit}
              disabled={stopping || stopped}
              className="flex items-center gap-2 rounded-full border border-rose-300/25 bg-rose-300/10 px-3 py-1.5 text-xs text-rose-100 transition hover:bg-rose-300/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Power className="size-3.5" />
              {stopping ? "Arresto…" : "Esci"}
            </button>
          </div>
        </header>

        {error && (
          <div className="mt-4 rounded-2xl border border-amber-300/25 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
            {error} Avvia Luca con <code>python run_luca.py</code>.
          </div>
        )}
        {stopped && (
          <div className="mt-4 rounded-2xl border border-emerald-300/25 bg-emerald-300/10 px-4 py-3 text-sm text-emerald-100">
            Luca è stato arrestato correttamente. Puoi chiudere questa scheda.
          </div>
        )}

        <section className="grid flex-1 gap-5 py-6 xl:grid-cols-[330px_minmax(0,1fr)_360px]">
          <aside className="order-2 flex max-h-[780px] flex-col rounded-3xl border border-white/10 bg-white/[.035] p-5 xl:order-1">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[.18em] text-slate-400">
                SSD · Cervello Completo ({state.memory.length})
              </p>
              <span className="text-[11px] text-cyan-200/80">Clicca per catapultare in VRAM</span>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto pr-1">
              {state.memory.map((item) => {
                const inVram = vramNodes.some((n) => n.id === item.id);
                const inRam = ramNodes.some((n) => n.id === item.id);
                return (
                  <button
                    key={item.id}
                    onClick={() => recallNode(item.id)}
                    className={`w-full rounded-2xl border p-3.5 text-left transition ${
                      inVram
                        ? "border-cyan-300/40 bg-cyan-300/10"
                        : inRam
                        ? "border-violet-300/30 bg-violet-400/10"
                        : "border-white/8 bg-black/20 hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`size-2 rounded-full ${
                            inVram ? "bg-cyan-300" : inRam ? "bg-violet-300" : "bg-slate-600"
                          }`}
                        />
                        <span className="text-sm font-medium">
                          #{item.id} {item.label}
                        </span>
                      </div>
                      <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-300">
                        {inVram ? "VRAM" : inRam ? "RAM" : "SSD"}
                      </span>
                    </div>
                    {item.content && <p className="mt-1.5 line-clamp-2 text-xs text-slate-400">{item.content}</p>}
                    {item.facts.slice(0, 3).map((fact, idx) => (
                      <p key={`${item.id}-${idx}`} className="mt-1 pl-3 font-mono text-[11px] text-cyan-200/75">
                        {fact.predicate} → {fact.object}
                      </p>
                    ))}
                  </button>
                );
              })}
            </div>
          </aside>

          <section className="flex min-h-[580px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#101522]/80 shadow-2xl shadow-black/30">
            <div className="flex items-center justify-between border-b border-white/8 px-6 py-4">
              <div>
                <p className="text-sm font-medium">Conversazione & Attivazione Sinaptica</p>
                <p className="text-xs text-slate-500">Sessione · Christian · adapter {state.adapter}</p>
              </div>
              <Sparkles className="size-5 text-cyan-200" />
            </div>
            <div className="flex-1 space-y-5 overflow-y-auto p-6">
              {messages.length === 0 && (
                <p className="text-sm text-slate-500">
                  La conversazione apparirà qui quando Luca riceverà il primo messaggio.
                </p>
              )}
              {messages.map((message, i) => (
                <div
                  key={i}
                  className={message.role === "Christian" ? "ml-auto max-w-[82%]" : "mr-auto max-w-[82%]"}
                >
                  <p className="mb-1 text-[11px] uppercase tracking-[.14em] text-slate-500">{message.role}</p>
                  <div
                    className={
                      message.role === "Christian"
                        ? "rounded-2xl rounded-tr-sm bg-cyan-300 px-4 py-3 text-sm text-slate-950"
                        : "rounded-2xl rounded-tl-sm border border-white/8 bg-white/[.055] px-4 py-3 text-sm"
                    }
                  >
                    {message.text}
                  </div>
                  {message.trace && (
                    <p className="mt-2 font-mono text-[11px] text-cyan-200/70">VRAM trace: {message.trace}</p>
                  )}
                </div>
              ))}
              {sending && <p className="text-xs text-slate-500">Luca sta elaborando…</p>}
            </div>
            <div className="border-t border-white/8 p-4">
              <div className="flex gap-3 rounded-2xl border border-white/10 bg-black/20 p-2 pl-4 focus-within:border-cyan-300/40">
                <input
                  value={input}
                  disabled={sending || stopping || stopped}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => event.key === "Enter" && send()}
                  placeholder="Chiedi a Luca (es. giostra, cesare, archi prefisso suffisso, oblio)…"
                  className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-600"
                />
                <button
                  onClick={send}
                  disabled={sending || stopping || stopped || state.status !== "ready"}
                  className="grid size-10 place-items-center rounded-xl bg-cyan-300 text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Invia"
                >
                  <ArrowUp className="size-5" />
                </button>
              </div>
            </div>
          </section>

          <aside className="order-1 flex max-h-[780px] flex-col gap-4 overflow-y-auto xl:order-3">
            <div className="rounded-3xl border border-cyan-300/25 bg-cyan-300/5 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-cyan-200">
                  <Cpu className="size-4" />
                  <span className="text-xs font-semibold uppercase tracking-[.15em]">VRAM · Fuoco Attivo</span>
                </div>
                <span className="font-mono text-xs text-cyan-200">
                  {vramNodes.length} / {vramCap} slot
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                Testa = appena richiamato. Clicca un nodo di 1° grado per spostare il pensiero.
              </p>
              <div className="mt-3 space-y-2.5">
                {vramNodes.length === 0 && <p className="text-xs text-slate-500">Nessun nodo in VRAM.</p>}
                {vramNodes.map((node, index) => (
                  <button
                    key={node.id}
                    onClick={() => recallNode(node.id)}
                    className={`w-full rounded-2xl border p-3 text-left transition ${
                      node.expanded
                        ? "border-cyan-300/45 bg-cyan-300/15"
                        : "border-white/10 bg-black/30 hover:border-cyan-300/30"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-100">
                        {index + 1}. #{node.id} {node.title}
                      </span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] ${
                          node.expanded ? "bg-cyan-300 text-slate-950 font-semibold" : "bg-white/10 text-slate-300"
                        }`}
                      >
                        {node.expanded ? "Centro 1°" : "Confine 1°"}
                      </span>
                    </div>
                    <p className="mt-1 line-clamp-2 text-[11px] text-slate-300">{node.content}</p>
                    <p className="mt-1 font-mono text-[10px] text-cyan-200/75">
                      *:{node.slug} [{node.incoming_ids.join(",") || "-"}] | {node.slug}:* [
                      {node.outgoing_ids.join(",") || "-"}]
                    </p>
                  </button>
                ))}
              </div>
              {chains.length > 0 && (
                <div className="mt-3 rounded-2xl border border-white/10 bg-black/30 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-cyan-200">
                    Catene Auto-Ordinate (Prefisso → Suffisso)
                  </p>
                  {chains.slice(0, 4).map((chain, idx) => (
                    <p key={idx} className="mt-1 font-mono text-[11px] text-slate-300">
                      {chain.join(" → ")}
                    </p>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-3xl border border-violet-300/20 bg-violet-400/10 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-violet-200">
                  <Layers className="size-4" />
                  <span className="text-xs font-semibold uppercase tracking-[.15em]">RAM · Scivolati da VRAM</span>
                </div>
                <span className="font-mono text-xs text-violet-200">
                  {ramNodes.length} / {ramCap} slot
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400">
                Nodi meno recenti espulsi dalla VRAM; scenderanno in SSD se non richiamati.
              </p>
              <div className="mt-3 space-y-2">
                {ramNodes.length === 0 && <p className="text-xs text-slate-500">Nessun nodo ancora scivolato in RAM.</p>}
                {ramNodes.map((node, index) => (
                  <button
                    key={node.id}
                    onClick={() => recallNode(node.id)}
                    className="w-full rounded-xl border border-white/10 bg-black/25 p-2.5 text-left transition hover:border-violet-300/40"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-200">
                        {index + 1}. #{node.id} {node.title}
                      </span>
                      <span className="text-[10px] text-violet-200">Richiami: {node.recall_count}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/[.035] p-5">
              <div className="flex items-center justify-between text-slate-400">
                <div className="flex items-center gap-2">
                  <Database className="size-4" />
                  <span className="text-xs uppercase tracking-[.15em]">SSD · Persistenza</span>
                </div>
                <span className="font-mono text-xs text-slate-200">{state.storage.ssd_label}</span>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                <Activity className="size-4 text-cyan-200" />
                <span>Totale celle su disco: {state.working_set.ssd_cells ?? state.memory.length}</span>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
