"use strict";

const THEME_KEY = "cesare-gui-theme";
const NAV_COLLAPSED_KEY = "cesare-gui-nav-collapsed";

const PAGE_META = {
  chat: { eyebrow: "LAVORO", title: "Chat & Attivazione Sinaptica" },
  memory: { eyebrow: "MEMORIA & SINAPSI", title: "Livelli VRAM · RAM · SSD" },
  graphs: { eyebrow: "MEMORIA & SINAPSI", title: "Grafo Domino (prefisso:suffisso)" },
  operational: { eyebrow: "SISTEMA", title: "Stato Operativo & Diagnostica" },
};

let appState = null;
let messages = [];
let busy = false;
let stopped = false;
let currentPage = "chat";

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

function applyTheme(theme) {
  const valid = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = valid;
  localStorage.setItem(THEME_KEY, valid);
  const select = $("theme-select");
  if (select && select.value !== valid) select.value = valid;
}

function setBusy(isBusy) {
  busy = isBusy;
  if (appState) renderConvergence(appState);
  const hamster = $("hamster-indicator");
  if (hamster) hamster.style.display = isBusy ? "inline-flex" : "none";
  const submitBtn = $("chat-submit-btn");
  if (submitBtn) submitBtn.disabled = isBusy || stopped;
}

function showError(msg) {
  const box = $("alert-box");
  if (!box) return;
  if (!msg) {
    box.style.display = "none";
    box.textContent = "";
    return;
  }
  box.className = "notice error";
  box.textContent = msg;
  box.style.display = "block";
}

function switchPage(pageId) {
  if (!PAGE_META[pageId]) return;
  currentPage = pageId;
  $("page-eyebrow").textContent = PAGE_META[pageId].eyebrow;
  $("page-title").textContent = PAGE_META[pageId].title;
  ["chat", "memory", "graphs", "operational"].forEach((id) => {
    const el = $("view-" + id);
    if (el) el.style.display = id === pageId ? (id === "chat" ? "grid" : "block") : "none";
  });
  document.querySelectorAll(".nav-item[data-page]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === pageId);
  });
  if (appState) renderAll(appState);
}

function renderTranscript() {
  const container = $("chat-transcript");
  if (!container) return;
  if (!messages.length) {
    container.innerHTML = `<div class="empty">Connessione al nucleo sinaptico di Luca in corso…</div>`;
    return;
  }
  container.innerHTML = messages
    .map((msg) => {
      const isUser = msg.role === "Christian";
      const roleClass = isUser ? "user" : "assistant";
      const traceBadge = msg.trace
        ? `<span class="edge-pill" title="Celle attive in VRAM in questo turno">VRAM trace: ${escapeHtml(msg.trace)}</span>`
        : "";
      return `
        <article class="card chat-message ${roleClass}">
          <header class="message-head">
            <span>${escapeHtml(msg.role)}</span>
            ${traceBadge}
          </header>
          <div class="message-content">${escapeHtml(msg.text)}</div>
        </article>
      `;
    })
    .join("");
  container.scrollTop = container.scrollHeight;
}

function renderChatSidebar(state) {
  const vramNodes = state.tiers?.vram?.nodes || [];
  const ramNodes = state.tiers?.ram?.nodes || [];
  const chains = state.tiers?.vram?.chains || [];
  const families = state.tiers?.vram?.families || [];
  const vramCap = state.tiers?.vram?.capacity || 5;
  const ramCap = state.tiers?.ram?.capacity || 12;
  const memory = state.memory || [];

  $("vram-counter").textContent = `${vramNodes.length} / ${vramCap}`;
  $("ram-counter").textContent = `${ramNodes.length} / ${ramCap}`;
  $("ssd-counter").textContent = `${memory.length} nodi`;

  const chainHtml = chains.map((c) => `<div class="chain-box"><strong>Catena:</strong> ${escapeHtml(c.join("  →  "))}</div>`);
  const familyHtml = families.map(
    (f) =>
      `<div class="chain-box"><strong>Famiglia ${escapeHtml(f.pattern)} (${escapeHtml(f.slug_pattern)}):</strong> ${escapeHtml(
        f.member_ids.map((id) => "#" + id).join(", ")
      )}</div>`
  );
  $("chains-list").innerHTML =
    chainHtml.length || familyHtml.length
      ? [...chainHtml, ...familyHtml].join("")
      : `<div class="muted" style="font-size:var(--text-xs);">Nessuna catena o famiglia attiva. Avvia il dialogo o clicca un nodo.</div>`;


  $("vram-list").innerHTML = vramNodes.length
    ? vramNodes
        .map(
          (n) => `
        <button type="button" class="tier-item tier-vram ${n.expanded ? "expanded" : ""}" data-recall-id="${n.id}">
          <div class="tier-item-head">
            <span class="tier-item-title">#${n.id} ${escapeHtml(n.title)}</span>
            <span class="tier-badge ${n.expanded ? "vram-center" : "vram"}">${
            n.expanded ? "CENTRO ESPANSO" : "1° GRADO"
          }</span>
          </div>
          <p class="tier-item-desc">${escapeHtml(n.content)}</p>
          <div class="tier-item-edges">
            ${n.incoming_ids.map((id) => `<span class="edge-pill">${id}:${n.id}</span>`).join("")}
            ${n.outgoing_ids.map((id) => `<span class="edge-pill">${n.id}:${id}</span>`).join("")}
          </div>
        </button>`
        )
        .join("")
    : `<div class="muted" style="font-size:var(--text-xs);">VRAM vuota.</div>`;

  $("ram-list").innerHTML = ramNodes.length
    ? ramNodes
        .map(
          (n) => `
        <button type="button" class="tier-item tier-ram" data-recall-id="${n.id}">
          <div class="tier-item-head">
            <span class="tier-item-title">#${n.id} ${escapeHtml(n.title)}</span>
            <span class="tier-badge ram">RAM · x${n.recall_count}</span>
          </div>
          <p class="tier-item-desc">${escapeHtml(n.content)}</p>
        </button>`
        )
        .join("")
    : `<div class="muted" style="font-size:var(--text-xs);">Nessun nodo in RAM.</div>`;

  const vramIds = new Set(vramNodes.map((n) => n.id));
  const ramIds = new Set(ramNodes.map((n) => n.id));

  $("ssd-list").innerHTML = memory
    .map((item) => {
      const inVram = vramIds.has(item.id);
      const inRam = ramIds.has(item.id);
      const badgeClass = inVram ? "vram" : inRam ? "ram" : "";
      const badgeLabel = inVram ? "VRAM" : inRam ? "RAM" : "SSD";
      return `
        <button type="button" class="tier-item ${inVram ? "tier-vram" : inRam ? "tier-ram" : ""}" data-recall-id="${item.id}">
          <div class="tier-item-head">
            <span class="tier-item-title">#${item.id} ${escapeHtml(item.label)}</span>
            <span class="tier-badge ${badgeClass}">${badgeLabel}</span>
          </div>
          ${item.content ? `<p class="tier-item-desc">${escapeHtml(item.content)}</p>` : ""}
        </button>`;
    })
    .join("");
}

function renderMemoryTables(state) {
  const vramNodes = state.tiers?.vram?.nodes || [];
  const ramNodes = state.tiers?.ram?.nodes || [];
  const memory = state.memory || [];
  const vramCap = state.tiers?.vram?.capacity || 5;
  const ramCap = state.tiers?.ram?.capacity || 12;

  $("memory-metrics").innerHTML = `
    <div><span>Celle in VRAM</span><strong>${vramNodes.length} / ${vramCap}</strong></div>
    <div><span>Celle in RAM (LRU)</span><strong>${ramNodes.length} / ${ramCap}</strong></div>
    <div><span>Totale Nodi in SSD</span><strong>${memory.length}</strong></div>
    <div><span>Dimensione SSD SQLite</span><strong>${escapeHtml(state.storage?.ssd_label || "0.00 MB")}</strong></div>
  `;

  $("table-vram-body").innerHTML = vramNodes.length
    ? vramNodes
        .map(
          (n) => `
      <tr>
        <td><strong>#${n.id}</strong></td>
        <td><strong>${escapeHtml(n.title)}</strong><br><small class="muted">${escapeHtml(n.slug)}</small></td>
        <td><span class="tier-badge ${n.expanded ? "vram-center" : "vram"}">${
            n.expanded ? "Centro Espanso" : "1° Grado"
          }</span></td>
        <td>
          ${n.incoming_ids.map((id) => `<span class="edge-pill">${id}:${n.id}</span>`).join(" ")}
          ${n.outgoing_ids.map((id) => `<span class="edge-pill">${n.id}:${id}</span>`).join(" ")}
        </td>
        <td>${escapeHtml(n.content)}</td>
        <td><button type="button" class="secondary" data-recall-id="${n.id}" style="min-height:32px;padding:4px 10px;font-size:.78rem;">Espandi 1° grado</button></td>
      </tr>`
        )
        .join("")
    : `<tr><td colspan="6" class="empty">Nessuna cella attualmente in VRAM.</td></tr>`;

  $("table-ram-body").innerHTML = ramNodes.length
    ? ramNodes
        .map(
          (n) => `
      <tr>
        <td><strong>#${n.id}</strong></td>
        <td><strong>${escapeHtml(n.title)}</strong><br><small class="muted">${escapeHtml(n.slug)}</small></td>
        <td>${n.recall_count}</td>
        <td>${escapeHtml(n.content)}</td>
        <td><button type="button" class="secondary" data-recall-id="${n.id}" style="min-height:32px;padding:4px 10px;font-size:.78rem;">Riporta in VRAM</button></td>
      </tr>`
        )
        .join("")
    : `<tr><td colspan="5" class="empty">Nessuna cella in RAM.</td></tr>`;

  const vramIds = new Set(vramNodes.map((n) => n.id));
  const ramIds = new Set(ramNodes.map((n) => n.id));

  $("table-ssd-body").innerHTML = memory
    .map((item) => {
      const inVram = vramIds.has(item.id);
      const inRam = ramIds.has(item.id);
      const tierBadge = inVram
        ? `<span class="tier-badge vram">VRAM</span>`
        : inRam
        ? `<span class="tier-badge ram">RAM</span>`
        : `<span class="tier-badge">SSD</span>`;
      const factsHtml = (item.facts || [])
        .map((f) => `<span class="edge-pill">${escapeHtml(f.predicate)} → ${escapeHtml(f.object)}</span>`)
        .join(" ");
      return `
      <tr>
        <td><strong>#${item.id}</strong></td>
        <td><strong>${escapeHtml(item.label)}</strong><br><small class="muted">${escapeHtml(item.slug || "")}</small></td>
        <td>${tierBadge}</td>
        <td>${factsHtml || "—"}</td>
        <td>${escapeHtml(item.content || "")}</td>
        <td><button type="button" class="secondary" data-recall-id="${item.id}" style="min-height:32px;padding:4px 10px;font-size:.78rem;">Catapulta in VRAM</button></td>
      </tr>`;
    })
    .join("");
}

function renderSynapticGraph(state) {
  const svg = $("synaptic-graph-svg");
  if (!svg) return;
  const memory = state.memory || [];
  const vramNodes = state.tiers?.vram?.nodes || [];
  const ramNodes = state.tiers?.ram?.nodes || [];
  const chains = state.tiers?.vram?.chains || [];
  const vramMap = new Map(vramNodes.map((n) => [n.id, n]));
  const ramSet = new Set(ramNodes.map((n) => n.id));

  // Layout nodes in structured rows (identity #1 at top, then chains of 4)
  const positions = new Map();
  memory.forEach((node, idx) => {
    if (node.id === 1) {
      positions.set(node.id, { x: 110, y: 220 });
    } else {
      const rel = idx - 1;
      const row = Math.floor(rel / 4);
      const col = rel % 4;
      positions.set(node.id, {
        x: 310 + col * 225,
        y: 95 + row * 125,
      });
    }
  });

  // Build edges from facts
  const labelToId = new Map(memory.map((m) => [m.label, m.id]));
  const edges = [];
  memory.forEach((m) => {
    (m.facts || []).forEach((f) => {
      if (f.predicate.endsWith(":*")) {
        const targetId = labelToId.get(f.object);
        if (targetId) edges.push({ source: m.id, target: targetId });
      }
    });
  });

  const edgesHtml = edges
    .map((e) => {
      const p1 = positions.get(e.source);
      const p2 = positions.get(e.target);
      if (!p1 || !p2) return "";
      const active = vramMap.has(e.source) && vramMap.has(e.target);
      const stroke = active ? "#60a5fa" : "#64748b";
      const width = active ? 3 : 1.5;
      const opacity = active ? 0.95 : 0.45;
      return `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${stroke}" stroke-width="${width}" stroke-opacity="${opacity}" />`;
    })
    .join("");

  const nodesHtml = memory
    .map((m) => {
      const pos = positions.get(m.id);
      if (!pos) return "";
      const vNode = vramMap.get(m.id);
      const inRam = ramSet.has(m.id);
      let fill = "#475569";
      let stroke = "#94a3b8";
      if (vNode) {
        fill = vNode.expanded ? "#2563eb" : "#10b981";
        stroke = "#ffffff";
      } else if (inRam) {
        fill = "#d97706";
        stroke = "#fde68a";
      }
      const shortLabel = m.label.length > 22 ? m.label.slice(0, 20) + "…" : m.label;
      return `
        <g class="graph-node" data-recall-id="${m.id}" style="cursor:pointer;">
          <circle cx="${pos.x}" cy="${pos.y}" r="${vNode?.expanded ? 22 : 18}" fill="${fill}" stroke="${stroke}" stroke-width="2.2" />
          <text x="${pos.x}" y="${pos.y + 4}" text-anchor="middle" fill="#ffffff" font-size="11" font-weight="700">#${m.id}</text>
          <text x="${pos.x}" y="${pos.y + 36}" text-anchor="middle" fill="#e2e8f0" font-size="12" font-weight="600">${escapeHtml(shortLabel)}</text>
        </g>`;
    })
    .join("");

  svg.innerHTML = edgesHtml + nodesHtml;

  $("graph-chains-detail").innerHTML = chains.length
    ? chains.map((c) => `<div class="chain-box">${escapeHtml(c.join("  →  "))}</div>`).join("")
    : `<div class="muted">Nessuna catena attiva in VRAM. Clicca un nodo sul grafo sopra per attivare il richiamo di 1° grado.</div>`;
}

function renderConvergence(state) {
  const result = state.convergence || state.previous_convergence;
  const summary = $("convergence-summary");
  const alternatives = $("convergence-alternatives");
  if (!result) {
    summary.textContent = "Nessuna ricerca eseguita. Politica: " + (state.memory_search_policy === "complete" ? "completa" : "rapida");
    alternatives.innerHTML = "";
    return;
  }
  const times = result.timings_ms || {};
  const scope = result.ranking_is_global ? "grafo completo, risultati limitati" : "candidati più utilizzati, graduatoria non globale";
  summary.textContent = `${result.historical ? "Ultima ricerca (storico)" : "Ricerca corrente"} · ${result.mode} · ${scope}. ` +
    `Strategia: ${result.strategy}. Aperti: ${result.opened_ids.join(", ") || "nessuno"}. ` +
    `Selezione ${times.selection} ms · Query ${times.query} ms · Richiamo totale ${times.recall} ms. ` +
    `Archi seed stimati: ${result.estimated_seed_edges}. ` +
    (result.status_label ? "Nessuna corrispondenza completa; le alternative sono parziali." : "");
  alternatives.innerHTML = (result.alternatives || []).map((candidate) =>
    `<button type="button" class="secondary" data-alternative-id="${candidate.id}" ${busy || stopped ? "disabled" : ""}>` +
    `Apri #${candidate.id} · ${escapeHtml(candidate.title)} (${candidate.matched_required}/${candidate.required_total})</button>`
  ).join("");
}

function renderOperational(state) {
  const vramNodes = state.tiers?.vram?.nodes || [];
  const ramNodes = state.tiers?.ram?.nodes || [];
  const memory = state.memory || [];
  $("op-metrics").innerHTML = `
    <div><span>Stato Server</span><strong>${state.status === "ready" ? "Operativo (Ready)" : "Arrestato"}</strong></div>
    <div><span>Adapter Linguistico</span><strong>${escapeHtml(state.adapter || "gemma")}</strong></div>
    <div><span>Celle in VRAM</span><strong>${vramNodes.length} / ${state.tiers?.vram?.capacity || 5}</strong></div>
    <div><span>Celle in RAM</span><strong>${ramNodes.length} / ${state.tiers?.ram?.capacity || 12}</strong></div>
    <div><span>Nodi Totali in SSD</span><strong>${memory.length}</strong></div>
    <div><span>Peso Database SQLite</span><strong>${escapeHtml(state.storage?.ssd_label || "0.00 MB")}</strong></div>
  `;
}

function renderMemoryControls(state) {
  const request = state.model_request || {};
  const context = state.context_budget || {};
  const vram = state.tiers?.vram || {};
  const ram = state.tiers?.ram || {};
  const plan = state.recall_plan;
  const physical = state.physical_memory || {};
  $("physical-memory-status").textContent = physical.physical_vram
    ? `Memoria GPU reale · GPU ${physical.device_index} · ${physical.device_name} · ${physical.allocated_bytes} byte allocati · ${physical.allocations} buffer`
    : "Modalità HOST di riferimento: entrambi i livelli sono in RAM, nessuna VRAM GPU utilizzata.";
  $("context-status").textContent = (plan ? `Piano: ${plan.operation} (${plan.source}). ${plan.reason} ` : "") +
    `Politica: ${state.memory_policy || "grounded"}. Richiesta: ${request.input_units ?? "—"}/${request.input_limit ?? "—"} unità UTF-8 conservative; ` +
    `riserva risposta ${request.output_reserve ?? "—"}. Memoria esposta: ${context.input_units ?? 0}/${context.limit ?? "—"}. ` +
    (physical.physical_vram
      ? `VRAM fisica: GPU ${physical.device_index} (${physical.device_name}), ${physical.allocated_bytes} byte in ${physical.allocations} allocazioni; trasferiti RAM→GPU ${physical.upload_bytes} byte, GPU→RAM ${physical.download_bytes} byte; caricamenti SQLite ${physical.disk_loads} (${physical.disk_payload_bytes} byte di payload). `
      : "Modalità HOST: primo livello in RAM, nessuna allocazione VRAM fisica. ") +
    `Payload livelli: attivo ${vram.payload_bytes ?? 0}/${vram.max_bytes ?? "—"} byte; RAM ${ram.payload_bytes ?? 0}/${ram.max_bytes ?? "—"} byte. ` +
    `Estratti parziali: ${(context.truncated_ids || []).join(", ") || "nessuno"}.`;
  $("document-sections").innerHTML = (state.memory || []).flatMap(node => (node.sections || []).map(section =>
    `<button type="button" class="secondary" data-section-node="${node.id}" data-section-key="${encodeURIComponent(section.key)}">` +
    `${escapeHtml(node.label)} / ${escapeHtml(section.title)}</button>`
  )).join("");
  const task = state.task || {};
  $("task-status").textContent = task.active
    ? `${task.goal || "Compito attivo"} · ${task.suspended ? "Sospeso durante la consultazione di un altro argomento" : "In corso"} · Punto di ripresa: #${task.focus_id ?? "—"} · ${task.input_units}/${task.limit} unità`
    : "Nessun compito attivo. Puoi anche scrivere Obiettivo:, Vincolo: o Decisione: nella chat.";
  const fields = {"task-goal": task.goal || "", "task-constraints": (task.constraints || []).join("\n"), "task-decisions": (task.decisions || []).join("\n")};
  for (const [id, value] of Object.entries(fields)) {
    if (document.activeElement !== $(id)) $(id).value = value;
  }
}

function renderAll(state) {
  appState = state;
  const badge = $("status-badge");
  const statusText = $("status-text");
  if (stopped || state.status !== "ready") {
    badge.className = "status offline";
    statusText.textContent = stopped ? "Luca arrestato" : "Offline";
  } else {
    badge.className = "status";
    statusText.textContent = `Sinapsi attive · adapter ${state.adapter}`;
  }

  $("sum-vram").textContent = state.working_set?.vram_cells ?? 0;
  $("sum-ram").textContent = state.working_set?.ram_cells ?? 0;
  $("sum-ssd").textContent = state.working_set?.ssd_cells ?? (state.memory?.length || 0);
  $("sum-mb").textContent = state.storage?.ssd_label || "0.00 MB";
  $("sum-adapter").textContent = state.adapter || "gemma";

  const trace = state.working_set?.trace || [];
  $("trace-last-label").textContent = trace.length
    ? `VRAM attiva: ${trace.join(" → ")}`
    : "VRAM attiva: —";

  renderChatSidebar(state);
  renderMemoryTables(state);
  renderSynapticGraph(state);
  renderOperational(state);
  renderConvergence(state);
  renderMemoryControls(state);
}

async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Errore HTTP ${response.status}`);
  }
  return payload;
}

async function sendChat(text) {
  if (!text || busy || stopped) return;
  setBusy(true);
  showError("");
  messages.push({ role: "Christian", text });
  renderTranscript();
  try {
    const payload = await apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    messages.push({
      role: "Luca",
      text: payload.reply.text,
      trace: payload.reply.trace?.length ? payload.reply.trace.join(" → ") : "",
    });
    renderTranscript();
    renderAll(payload.state);
  } catch (err) {
    showError(err.message || "Errore di comunicazione con Luca.");
  } finally {
    setBusy(false);
  }
}

async function resetSession() {
  if (busy || stopped) return;
  setBusy(true);
  showError("");
  try {
    const payload = await apiFetch("/api/reset", { method: "POST", body: "{}" });
    messages = [{ role: "Luca", text: payload.reply.text, trace: "" }];
    renderTranscript();
    renderAll(payload.state);
  } catch (err) {
    showError(err.message || "Impossibile azzerare la sessione.");
  } finally {
    setBusy(false);
  }
}

async function recallNode(nodeId, alternative = false) {
  if (busy || stopped) return;
  setBusy(true);
  showError("");
  try {
    const payload = await apiFetch(alternative ? "/api/alternative" : "/api/recall", {
      method: "POST",
      body: JSON.stringify({ node_id: Number(nodeId) }),
    });
    if (payload.state) renderAll(payload.state);
  } catch (err) {
    showError(err.message || "Errore durante il richiamo sinaptico.");
  } finally {
    setBusy(false);
    if (appState) renderConvergence(appState);
  }
}

async function shutdownServer() {
  if (stopped) return;
  try {
    await apiFetch("/api/shutdown", { method: "POST", body: "{}" });
    stopped = true;
    if (appState) renderAll({ ...appState, status: "error" });
    const box = $("alert-box");
    box.className = "notice success";
    box.textContent = "Luca è stato arrestato correttamente. Puoi chiudere questa scheda.";
    box.style.display = "block";
  } catch (err) {
    showError(err.message || "Errore durante l'arresto di Luca.");
  }
}

async function openSection(nodeId, key) {
  if (busy || stopped) return;
  setBusy(true);
  try {
    const result = await apiFetch("/api/section", {method: "POST", body: JSON.stringify({node_id: Number(nodeId), key})});
    renderAll(result.state);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
}

async function updateTask(values) {
  if (busy || stopped) return;
  setBusy(true);
  try {
    const result = await apiFetch("/api/task", {method: "POST", body: JSON.stringify(values)});
    renderAll(result.state);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
}

function bindEvents() {
  $("task-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const lines = id => $(id).value.split("\n").map(line => line.trim()).filter(Boolean);
    void updateTask({goal: $("task-goal").value, constraints: lines("task-constraints"), decisions: lines("task-decisions")});
  });
  $("task-clear-btn").addEventListener("click", () => void updateTask({clear: true}));
  $("task-resume-btn").addEventListener("click", () => void sendChat("Riprendi il compito"));
  const savedTheme = localStorage.getItem(THEME_KEY) || "light";
  applyTheme(savedTheme);

  $("theme-select").addEventListener("change", (e) => applyTheme(e.target.value));

  const shell = $("shell");
  if (localStorage.getItem(NAV_COLLAPSED_KEY) === "true") {
    shell.classList.add("nav-collapsed");
  }
  $("sidebar-collapse-btn").addEventListener("click", () => {
    shell.classList.add("nav-collapsed");
    localStorage.setItem(NAV_COLLAPSED_KEY, "true");
  });
  $("brand-mark-btn").addEventListener("click", () => {
    if (shell.classList.contains("nav-collapsed")) {
      shell.classList.remove("nav-collapsed");
      localStorage.setItem(NAV_COLLAPSED_KEY, "false");
    }
  });

  document.querySelectorAll(".nav-group-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const expanded = btn.getAttribute("aria-expanded") === "true";
      const next = !expanded;
      btn.setAttribute("aria-expanded", String(next));
      const items = btn.parentElement.querySelector(".nav-group-items");
      const icon = btn.querySelector("i");
      if (items) items.style.display = next ? "grid" : "none";
      if (icon) icon.textContent = next ? "−" : "+";
    });
  });

  $("expand-all-groups").addEventListener("click", () => {
    document.querySelectorAll(".nav-group-toggle").forEach((btn) => {
      btn.setAttribute("aria-expanded", "true");
      const items = btn.parentElement.querySelector(".nav-group-items");
      const icon = btn.querySelector("i");
      if (items) items.style.display = "grid";
      if (icon) icon.textContent = "−";
    });
  });

  $("collapse-all-groups").addEventListener("click", () => {
    document.querySelectorAll(".nav-group-toggle").forEach((btn) => {
      btn.setAttribute("aria-expanded", "false");
      const items = btn.parentElement.querySelector(".nav-group-items");
      const icon = btn.querySelector("i");
      if (items) items.style.display = "none";
      if (icon) icon.textContent = "+";
    });
  });

  document.querySelectorAll(".nav-item[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => switchPage(btn.dataset.page));
  });

  $("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = $("chat-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    void sendChat(text);
  });

  $("chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      $("chat-form").requestSubmit();
    }
  });

  [$("sidebar-reset-btn"), $("topbar-reset-btn"), $("form-reset-btn"), $("op-reset-btn")].forEach((btn) => {
    if (btn) btn.addEventListener("click", () => void resetSession());
  });

  [$("sidebar-exit-btn"), $("op-exit-btn")].forEach((btn) => {
    if (btn) btn.addEventListener("click", () => void shutdownServer());
  });

  document.body.addEventListener("click", (e) => {
    const section = e.target.closest("[data-section-node]");
    if (section) {
      void openSection(section.dataset.sectionNode, decodeURIComponent(section.dataset.sectionKey));
      return;
    }
    const alternativeBtn = e.target.closest("[data-alternative-id]");
    if (alternativeBtn) {
      void recallNode(alternativeBtn.getAttribute("data-alternative-id"), true);
      return;
    }
    const recallBtn = e.target.closest("[data-recall-id]");
    if (recallBtn) {
      void recallNode(recallBtn.getAttribute("data-recall-id"));
    }
  });
}

async function init() {
  bindEvents();
  setBusy(true);
  try {
    const state = await apiFetch("/api/state");
    renderAll(state);
    const greet = await apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ text: "Ciao" }),
    });
    messages = [{ role: "Luca", text: greet.reply.text, trace: "" }];
    renderTranscript();
    renderAll(greet.state);
  } catch (err) {
    showError(err.message || "Impossibile contattare il server di Luca.");
  } finally {
    setBusy(false);
  }
}

document.addEventListener("DOMContentLoaded", init);
