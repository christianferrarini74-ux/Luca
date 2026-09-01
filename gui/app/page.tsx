"use client";

import { useState } from "react";
import { Activity, ArrowUp, BrainCircuit, CircleDot, Database, Sparkles } from "lucide-react";

type Message = { role: "Christian" | "Luca"; text: string; trace?: string };
const initial: Message[] = [
  { role: "Luca", text: "Ciao Christian. La mia memoria è attiva." },
  { role: "Christian", text: "Parlami del sole." },
  { role: "Luca", text: "So che il sole scalda la pelle.", trace: "sole → asserto → scalda → pelle" },
];

export default function Home() {
  const [messages, setMessages] = useState(initial);
  const [input, setInput] = useState("");
  const [learned, setLearned] = useState(false);
  const send = () => {
    const text = input.trim(); if (!text) return;
    const q = text.toLowerCase(); let response: Message;
    if (q.includes("ricorda") && q.includes("sole") && q.includes("luce")) { setLearned(true); response = { role: "Luca", text: "Ho registrato questa conoscenza nella memoria persistente.", trace: "sole → asserto → produce → luce" }; }
    else if (q.includes("produce") && (q.includes("sole") || learned)) response = learned ? { role: "Luca", text: "Il sole produce luce.", trace: "sole → asserto → produce → luce" } : { role: "Luca", text: "Non possiedo ancora una risposta verificata." };
    else if (q.includes("fuoco")) response = { role: "Luca", text: "So che il fuoco produce calore e scalda gli oggetti.", trace: "fuoco → asserto → produce → calore" };
    else response = { role: "Luca", text: "Questa è la GUI dimostrativa: presto la collegheremo al motore persistente di Luca." };
    setMessages([...messages, { role: "Christian", text }, response]); setInput("");
  };
  return <main className="min-h-screen bg-[#090b12] text-slate-100 selection:bg-cyan-300 selection:text-slate-950">
    <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_18%_0%,rgba(38,210,194,.16),transparent_34%),radial-gradient(circle_at_86%_12%,rgba(93,113,255,.16),transparent_27%)]" />
    <div className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col px-5 py-5 lg:px-8">
      <header className="flex items-center justify-between border-b border-white/10 pb-5"><div className="flex items-center gap-3"><div className="grid size-11 place-items-center rounded-2xl border border-cyan-300/30 bg-cyan-300/10"><BrainCircuit className="size-6 text-cyan-200" /></div><div><h1 className="text-xl font-semibold tracking-[.18em]">LUCA</h1><p className="text-xs tracking-wide text-slate-400">Persistent Cognitive Memory</p></div></div><div className="flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs text-emerald-200"><CircleDot className="size-3 fill-emerald-300" /> Memoria attiva</div></header>
      <section className="grid flex-1 gap-5 py-6 xl:grid-cols-[280px_minmax(0,1fr)_310px]">
        <aside className="order-2 rounded-3xl border border-white/10 bg-white/[.035] p-5 xl:order-1"><p className="mb-5 text-[11px] font-semibold uppercase tracking-[.18em] text-slate-500">Mappa della memoria</p><div className="space-y-4">{[["Sole","scalda → pelle"],["Fuoco","produce → calore"],["Forno","scalda → pane"],["Ghiaccio","raffredda → acqua"]].map(([name, detail]) => <div key={name} className="rounded-2xl border border-white/8 bg-black/20 p-3.5"><div className="flex items-center gap-2"><span className="size-2 rounded-full bg-cyan-300"/><span className="font-medium">{name}</span></div><p className="mt-1 pl-4 text-xs text-slate-400">{detail}</p></div>)}</div><div className="mt-6 rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-4 text-xs text-cyan-100">{learned ? "Nuova conoscenza consolidata" : "Insegna qualcosa a Luca"}<p className="mt-1 text-[11px] text-slate-400">Le celle restano. Il contesto passa.</p></div></aside>
        <section className="flex min-h-[580px] flex-col overflow-hidden rounded-3xl border border-white/10 bg-[#101522]/80 shadow-2xl shadow-black/30"><div className="flex items-center justify-between border-b border-white/8 px-6 py-4"><div><p className="text-sm font-medium">Conversazione</p><p className="text-xs text-slate-500">Sessione · Christian</p></div><Sparkles className="size-5 text-cyan-200"/></div><div className="flex-1 space-y-5 overflow-y-auto p-6">{messages.map((message, i) => <div key={i} className={message.role === "Christian" ? "ml-auto max-w-[82%]" : "mr-auto max-w-[82%]"}><p className="mb-1 text-[11px] uppercase tracking-[.14em] text-slate-500">{message.role}</p><div className={message.role === "Christian" ? "rounded-2xl rounded-tr-sm bg-cyan-300 px-4 py-3 text-sm text-slate-950" : "rounded-2xl rounded-tl-sm border border-white/8 bg-white/[.055] px-4 py-3 text-sm"}>{message.text}</div>{message.trace && <p className="mt-2 font-mono text-[11px] text-cyan-200/70">{message.trace}</p>}</div>)}</div><div className="border-t border-white/8 p-4"><div className="flex gap-3 rounded-2xl border border-white/10 bg-black/20 p-2 pl-4 focus-within:border-cyan-300/40"><input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&send()} placeholder="Scrivi o insegna a Luca…" className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-600"/><button onClick={send} className="grid size-10 place-items-center rounded-xl bg-cyan-300 text-slate-950" aria-label="Invia"><ArrowUp className="size-5"/></button></div></div></section>
        <aside className="order-1 grid gap-5 sm:grid-cols-3 xl:order-3 xl:grid-cols-1">{[["SSD","Cervello completo","14.2 MB","88%"],["RAM","Contesto attivo","46 celle","46%"],["VRAM","Focus del pensiero","12 celle","24%"]].map(([tier, description, value, width]) => <div key={tier} className="rounded-3xl border border-white/10 bg-white/[.035] p-5"><div className="flex items-center gap-2 text-slate-400"><Database className="size-4"/><span className="text-xs uppercase tracking-[.15em]">{tier}</span></div><p className="mt-6 text-xl font-medium">{value}</p><p className="mt-1 text-xs text-slate-400">{description}</p><div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/8"><div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400" style={{width}}/></div></div>)}<div className="rounded-3xl border border-violet-300/20 bg-violet-400/10 p-5"><Activity className="size-5 text-violet-200"/><p className="mt-3 text-sm font-medium">Pensiero tracciabile</p><p className="mt-1 text-xs leading-relaxed text-slate-400">Ogni risposta mostra il percorso nella memoria.</p></div></aside>
      </section>
    </div>
  </main>;
}
