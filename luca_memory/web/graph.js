/* Display-only topology projection and interaction; no memory policy lives here. */
"use strict";
(function (scope) {
  const validPoint = p => p && Number.isFinite(p.x) && Number.isFinite(p.y);

  function projectGraph(snapshot, expanded = new Set()) {
    const byId = new Map(snapshot.nodes.map(n => [n.id, n]));
    const representative = id => {
      const node = byId.get(id);
      return node && byId.has(node.root_id) && !expanded.has(node.root_id) ? node.root_id : id;
    };
    const nodes = snapshot.nodes.filter(n => representative(n.id) === n.id).map(n => ({...n}));
    const links = new Map();
    for (const edge of snapshot.edges) {
      const source = representative(edge.source), target = representative(edge.target);
      if (source === target && edge.source !== edge.target) continue;
      const key = `${source}:${target}`;
      if (!links.has(key)) links.set(key, {source, target, count:0, family:byId.get(edge.target)?.root_id === edge.source});
      links.get(key).count++;
    }
    return {nodes, edges:[...links.values()], representative};
  }

  function layoutGraph(nodes, edges, previous = new Map()) {
    const radius = Math.max(130, Math.sqrt(nodes.length) * 27);
    const points = new Map(nodes.map((n, i) => [n.id, validPoint(previous.get(n.id)) ?
      {x:previous.get(n.id).x, y:previous.get(n.id).y} :
      {x:Math.cos(i * 2.39996) * radius * Math.sqrt((i + 1) / nodes.length),
       y:Math.sin(i * 2.39996) * radius * Math.sqrt((i + 1) / nodes.length)}]));
    // Sample repulsion for large graphs, bounding work without changing topology.
    for (let iteration = 0; iteration < 65; iteration++) {
      const force = new Map(nodes.map(n => [n.id, {x:0, y:0}]));
      nodes.forEach((node, i) => {
        const p = points.get(node.id), f = force.get(node.id);
        const stride = Math.max(1, Math.floor(nodes.length / 64));
        for (let j = i % stride; j < nodes.length; j += stride) {
          if (j === i) continue;
          const q = points.get(nodes[j].id), dx = p.x - q.x, dy = p.y - q.y;
          const distance = Math.max(16, dx * dx + dy * dy);
          f.x += dx * 700 / distance; f.y += dy * 700 / distance;
        }
      });
      for (const e of edges) {
        const a = points.get(e.source), b = points.get(e.target);
        if (!a || !b || e.source === e.target) continue;
        const dx = b.x - a.x, dy = b.y - a.y, d = Math.max(1, Math.hypot(dx, dy));
        const amount = (d - 110) * .035;
        force.get(e.source).x += dx / d * amount; force.get(e.source).y += dy / d * amount;
        force.get(e.target).x -= dx / d * amount; force.get(e.target).y -= dy / d * amount;
      }
      for (const n of nodes) {
        const p = points.get(n.id), f = force.get(n.id);
        p.x += Math.max(-12, Math.min(12, f.x - p.x * .008));
        p.y += Math.max(-12, Math.min(12, f.y - p.y * .008));
      }
    }
    return points;
  }

  function fitCamera(points, width, height) {
    width = Number.isFinite(width) && width > 0 ? width : 800;
    height = Number.isFinite(height) && height > 0 ? height : 600;
    const finite = points.filter(validPoint);
    if (!finite.length) return {x:-width / 2, y:-height / 2, w:width, h:height};
    const xs = finite.map(p => p.x), ys = finite.map(p => p.y);
    const left = Math.min(...xs), right = Math.max(...xs), top = Math.min(...ys), bottom = Math.max(...ys);
    // Padding is measured in pixels because labels and hit targets have fixed screen size.
    const scale = Math.max(.75, (right - left) / Math.max(width * .2, width - 240),
                          (bottom - top) / Math.max(height * .2, height - 160));
    const w = width * scale, h = height * scale;
    return {x:(left + right - w) / 2, y:(top + bottom - h) / 2, w, h};
  }

  function traversedEdges(snapshot) {
    const roots = new Map(snapshot.nodes.map(n => [n.id, n.root_id]));
    return new Set((snapshot.navigation || []).filter(s => s.source === "local" && s.target_id).map(s =>
      `${roots.get(s.reading_id) ?? s.reading_id}:${roots.get(s.target_id) ?? s.target_id}`));
  }

  class MemoryGraph {
    constructor({fetchGraph, recall, isBusy}) {
      this.fetchGraph = fetchGraph; this.recall = recall; this.isBusy = isBusy;
      this.expanded = new Set(); this.positions = new Map(); this.selected = null;
      this.center = null; this.generation = 0; this.loading = false; this.signature = "";
      this.svg = document.getElementById("synaptic-graph-svg");
      this.el = id => document.getElementById("graph-" + id);
      this.camera = {x:-550, y:-300, w:1100, h:600};
      this.el("mode").addEventListener("change", () => {this.center = null; this.refresh(true);});
      this.el("search").addEventListener("input", () => this.draw());
      this.el("refresh").addEventListener("click", () => this.refresh());
      this.el("fit").addEventListener("click", () => this.fit());
      this.el("zoom-in").addEventListener("click", () => this.zoom(.8));
      this.el("zoom-out").addEventListener("click", () => this.zoom(1.25));
      this.el("family").addEventListener("click", () => {
        const root = this.node()?.root_id;
        if (this.expanded.has(root)) this.expanded.delete(root); else this.expanded.add(root);
        this.render(true);
      });
      this.el("neighborhood").addEventListener("click", () => {
        this.center = this.selected; this.el("mode").value = "focus"; this.refresh(true);
      });
      this.el("recall").addEventListener("click", async () => {
        if (this.selected === null || this.isBusy()) return;
        const id = this.selected;
        await this.recall(id); await this.refresh();
      });
      this.svg.addEventListener("keydown", e => {
        const target = e.target.closest("[data-graph-id]");
        if (target && (e.key === "Enter" || e.key === " ")) {e.preventDefault(); this.select(Number(target.dataset.graphId));}
      });
      this.svg.addEventListener("wheel", e => {e.preventDefault(); this.zoom(e.deltaY > 0 ? 1.12 : .89, this.point(e));}, {passive:false});
      this.svg.addEventListener("pointerdown", e => {
        if (e.button !== 0) return;
        const target = e.target.closest("[data-graph-id]");
        this.drag = {id:target ? Number(target.dataset.graphId) : null, start:this.point(e), x:e.clientX, y:e.clientY, camera:{...this.camera}, moved:false};
        this.svg.setPointerCapture(e.pointerId);
      });
      this.svg.addEventListener("pointermove", e => {
        if (!this.drag) return;
        const d = this.drag, p = this.point(e);
        d.moved ||= Math.hypot(e.clientX - d.x, e.clientY - d.y) > 4;
        if (d.id !== null) {this.positions.set(d.id, {x:p.x, y:p.y}); this.draw();}
        else {this.camera.x += d.start.x - p.x; this.camera.y += d.start.y - p.y; this.viewBox();}
      });
      const finish = e => {
        if (this.drag && !this.drag.moved && this.drag.id !== null) this.select(this.drag.id);
        this.drag = null;
        if (this.svg.hasPointerCapture(e.pointerId)) this.svg.releasePointerCapture(e.pointerId);
      };
      this.svg.addEventListener("pointerup", finish);
      this.svg.addEventListener("pointercancel", () => {this.drag = null;});
    }

    update(state) {
      this.el("recall").disabled = this.selected === null || this.isBusy();
      if (document.getElementById("view-graphs").style.display === "none") return;
      const key = JSON.stringify([state.synaptic, state.working_set]);
      if (key !== this.stateKey && !this.loading) {this.stateKey = key; void this.refresh();}
    }

    async refresh(fit = false) {
      const generation = ++this.generation;
      this.loading = true; this.el("status").textContent = "Lettura dei metadati della memoria…";
      try {
        const mode = this.el("mode").value;
        const data = await this.fetchGraph(`/api/graph?mode=${mode}` + (this.center !== null ? `&node_id=${this.center}` : ""));
        if (generation !== this.generation) return;
        this.snapshot = data; this.render(fit || !this.signature);
      } catch (e) {
        if (generation === this.generation) this.el("status").textContent = "Mappa non disponibile: " + e.message;
      } finally {if (generation === this.generation) this.loading = false;}
    }

    render(fit = false) {
      if (!this.snapshot) return;
      this.model = projectGraph(this.snapshot, this.expanded);
      const signature = JSON.stringify([this.model.nodes.map(n => n.id), this.model.edges]);
      if (signature !== this.signature) {
        this.drag = null;
        this.positions = layoutGraph(this.model.nodes, this.model.edges, this.positions);
        this.signature = signature;
      }
      if (!this.snapshot.nodes.some(n => n.id === this.selected)) this.selected = null;
      if (this.selected !== null) this.selected = this.model.representative(this.selected);
      const s = this.snapshot;
      const partial = s.nodes_truncated || s.edges_truncated;
      this.el("status").textContent = `${this.model.nodes.length} nodi visibili · ${s.nodes.length}/${s.scope_nodes} nodi nell'ambito (${s.total_nodes} totali) · ${s.edges.length}/${s.visible_edges} archi tra i nodi inclusi · revisione ${s.revision}` +
        ` · Focus Luca #${s.focus_id ?? "—"} / lettura #${s.reading_id ?? "—"}` +
        (s.mode === "focus" && s.center_id !== null ? ` · Vicinato di #${s.center_id}${this.center !== null ? " (esplorazione)" : " (focus Luca)"}` : "") +
        (partial ? " · VISTA PARZIALE: limiti frontend.graph in config.yaml. Esplora un vicinato per più dettaglio." : "") +
        (s.mode === "focus" && s.center_id === null ? " · Nessun focus: seleziona un nodo nella vista globale." : "") +
        (s.backend !== "cuda" ? " · Backend host: VRAM è un livello logico, non memoria GPU fisica." : "");
      const nav = this.el("navigation"); nav.replaceChildren();
      for (const step of s.navigation.filter(step => step.action === "open" && step.target_id)) {
        const item = document.createElement("li");
        item.textContent = step.source === "global" ? `Ingresso globale → #${step.target_id}` : `#${step.reading_id} → #${step.target_id} · rubrica locale`;
        nav.append(item);
      }
      if (!nav.children.length) {const li = document.createElement("li"); li.textContent = "Nessuna apertura registrata dal navigatore nell'ultimo turno."; nav.append(li);}
      this.draw(); this.inspect(); if (fit) this.fit();
    }

    node() {return this.snapshot?.nodes.find(n => n.id === this.selected);}
    select(id) {this.selected = id; this.draw(); this.inspect();}
    inspect() {
      const n = this.node();
      this.el("node-title").textContent = n ? n.title : "Seleziona un nodo";
      this.el("node-info").textContent = n ? `#${n.id} · ${n.tier.toUpperCase()} · famiglia #${n.root_id} · ${n.part_count} parti dirette. Nessun contenuto caricato dalla mappa.` : "Clic o Invio: metadati. Trascina: sposta nodo o mappa. Rotella: zoom.";
      const root = this.snapshot?.nodes.find(item => item.id === n?.root_id);
      if (n && root?.part_count) {
        const members = this.snapshot.nodes.filter(item => item.root_id === root.id);
        const counts = ["vram", "ram", "ssd"].map(tier => `${tier.toUpperCase()}: ${members.filter(item => item.tier === tier).length}`).join(" · ");
        this.el("node-info").textContent += ` Famiglia inclusa nella vista: ${counts}. Colore del padre = livello del padre, non delle parti.`;
      }
      this.el("family").disabled = !root?.part_count;
      this.el("family").textContent = this.expanded.has(n?.root_id) ? "Comprimi famiglia" : "Espandi famiglia";
      this.el("neighborhood").disabled = !n;
      this.el("recall").disabled = !n || this.isBusy();
    }

    element(tag, attrs = {}, text) {
      const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
      Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
      if (text !== undefined) el.textContent = text;
      return el;
    }
    draw() {
      if (!this.model) return;
      this.viewBox();
      const activeId = document.activeElement?.dataset?.graphId;
      const fragment = document.createDocumentFragment();
      // Keep labels and hit targets readable while zooming a large world-space layout.
      const scale = Math.max(this.camera.w / (this.svg.clientWidth || 800), this.camera.h / (this.svg.clientHeight || 600));
      const defs = this.element("defs"), marker = this.element("marker", {id:"graph-arrow", viewBox:"0 0 10 10", refX:9, refY:5, markerWidth:6, markerHeight:6, orient:"auto-start-reverse"});
      marker.append(this.element("path", {d:"M 0 0 L 10 5 L 0 10 z", fill:"#94a3b8"})); defs.append(marker); fragment.append(defs);
      const routes = traversedEdges(this.snapshot);
      for (const e of this.model.edges) {
        const a = this.positions.get(e.source), b = this.positions.get(e.target); if (!a || !b) continue;
        const d = Math.max(1, Math.hypot(b.x - a.x, b.y - a.y));
        const startInset = Math.min(18 * scale, d * .25), endInset = Math.min(22 * scale, d * .4);
        const path = e.source === e.target ? `M ${a.x-8} ${a.y-12} C ${a.x-55} ${a.y-65}, ${a.x+55} ${a.y-65}, ${a.x+8} ${a.y-12}` :
          `M ${a.x+(b.x-a.x)*startInset/d} ${a.y+(b.y-a.y)*startInset/d} L ${b.x-(b.x-a.x)*endInset/d} ${b.y-(b.y-a.y)*endInset/d}`;
        const line = this.element("path", {d:path, class:`memory-graph-edge${e.family ? " family" : ""}${routes.has(`${e.source}:${e.target}`) || routes.has(`${e.target}:${e.source}`) ? " traversed" : ""}`, "marker-end":"url(#graph-arrow)"});
        line.append(this.element("title", {}, `#${e.source} → #${e.target}${e.family ? " · parte della famiglia" : ""}`)); fragment.append(line);
      }
      const query = this.el("search").value.trim().toLocaleLowerCase();
      const read = new Set(this.snapshot.read_node_ids.map(id => this.model.representative(id)));
      for (const n of this.model.nodes) {
        const p = this.positions.get(n.id), selected = this.selected === n.id;
        if (!validPoint(p)) continue;
        const matches = !query || this.snapshot.nodes.some(item => this.model.representative(item.id) === n.id && `${item.id} ${item.title}`.toLocaleLowerCase().includes(query));
        const group = this.element("g", {transform:`translate(${p.x},${p.y}) scale(${scale})`, class:`memory-graph-node${selected ? " selected" : ""}${matches ? "" : " dim"}`, "data-graph-id":n.id, tabindex:0, role:"button", "aria-label":`#${n.id} ${n.title}, ${n.tier}`, "aria-pressed":String(selected)});
        if (n.id === this.model.representative(this.snapshot.focus_id)) group.append(this.element("circle", {r:24, class:"focus-ring"}));
        if (read.has(n.id)) group.append(this.element("circle", {r:28, class:"read-ring"}));
        group.append(this.element("circle", {r:n.part_count ? 18 : 14, fill:{vram:"#059669", ram:"#d97706", ssd:"#64748b"}[n.tier], stroke:"#fff", "stroke-width":1.5}));
        group.append(this.element("title", {}, `#${n.id} ${n.title} · ${n.tier.toUpperCase()}`));
        const title = n.title.length > 30 ? n.title.slice(0,28) + "…" : n.title;
        group.append(this.element("text", {y:43, "text-anchor":"middle"}, `#${n.id} ${title}${n.part_count && !this.expanded.has(n.id) ? ` (+${n.part_count})` : ""}`));
        fragment.append(group);
      }
      this.svg.replaceChildren(fragment); this.viewBox();
      if (activeId) this.svg.querySelector(`[data-graph-id="${Number(activeId)}"]`)?.focus({preventScroll:true});
    }
    point(e) {return new DOMPoint(e.clientX, e.clientY).matrixTransform(this.svg.getScreenCTM().inverse());}
    viewBox() {
      if (![this.camera.x, this.camera.y, this.camera.w, this.camera.h].every(Number.isFinite) || this.camera.w <= 0 || this.camera.h <= 0)
        this.camera = fitCamera([...this.positions.values()], this.svg.clientWidth, this.svg.clientHeight);
      const c = this.camera; this.svg.setAttribute("viewBox", `${c.x} ${c.y} ${c.w} ${c.h}`);
    }
    zoom(factor, at) {
      const c = this.camera, next = Math.max(100, Math.min(30000, c.w * factor));
      factor = next / c.w; at ||= {x:c.x+c.w/2, y:c.y+c.h/2};
      c.x = at.x - (at.x-c.x)*factor; c.y = at.y - (at.y-c.y)*factor; c.w *= factor; c.h *= factor; this.draw();
    }
    fit() {
      this.drag = null;
      const nodes = this.model?.nodes || [];
      if (nodes.some(n => !validPoint(this.positions.get(n.id))))
        this.positions = layoutGraph(nodes, this.model.edges);
      const points = nodes.map(n => this.positions.get(n.id));
      this.camera = fitCamera(points, this.svg.clientWidth, this.svg.clientHeight);
      this.draw();
    }
  }
  if (typeof module !== "undefined" && module.exports) module.exports = {projectGraph, layoutGraph, traversedEdges, fitCamera, MemoryGraph};
  else scope.MemoryGraph = MemoryGraph;
})(typeof window !== "undefined" ? window : globalThis);
