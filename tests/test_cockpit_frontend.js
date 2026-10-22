/* Run with node --test; all DOM, network, and timer effects stay inside the VM. */
"use strict";

const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const vm = require("node:vm");

const source = readFileSync(join(__dirname, "../luca_memory/web/app.js"), "utf8");

function element() {
  const listeners = {};
  const attributes = {};
  const classes = new Set();
  return {
    listeners, style: {}, dataset: {}, value: "", textContent: "", innerHTML: "",
    disabled: false,
    classList: {
      add: name => classes.add(name),
      remove: name => classes.delete(name),
      contains: name => classes.has(name),
      toggle(name, active) { if (active) classes.add(name); else classes.delete(name); },
    },
    addEventListener(name, callback) { listeners[name] = callback; },
    setAttribute(name, value) { attributes[name] = value; },
    getAttribute(name) { return attributes[name] ?? null; },
    querySelector() { return null; },
  };
}

function cockpit() {
  const elements = new Map();
  const groups = [];
  const calls = [];
  const renders = [];
  const timers = [];
  const cleared = [];
  const document = {
    ...element(), hidden: false, activeElement: null, body: element(),
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
    querySelectorAll(selector) { return selector === ".nav-group-toggle" ? groups : []; },
    documentElement: { dataset: {} },
  };
  const context = vm.createContext({
    document, window: element(),
    localStorage: { getItem() { return null; }, setItem() {} },
    setInterval(callback, delay) { timers.push({ callback, delay }); return timers.length; },
    clearInterval(id) { cleared.push(id); },
    async fetch(path, options) {
      calls.push({ path, options });
      return context.respond(path, options);
    },
    respond() { return { ok: true, json: async () => ({ state: { status: "ready" } }) }; },
    recordRender(state) { renders.push(state); },
  });
  vm.runInContext(source, context);
  // Isolate action/lifecycle behavior from unrelated HTML formatting and graph rendering.
  vm.runInContext(`
    renderAll = state => { appState = state; recordRender(state); };
    renderConvergence = () => {};
    renderTranscript = () => {};
  `, context);
  return {
    context, document, groups, calls, renders, timers, cleared,
    el: id => document.getElementById(id),
    run: code => vm.runInContext(code, context),
  };
}

test("section and task actions preserve payloads, alerts, snapshots, and busy guards", async () => {
  const app = cockpit();
  app.el("alert-box").textContent = "Existing alert";
  let complete;
  app.context.respond = () => new Promise(resolve => { complete = resolve; });
  const pending = app.run('openSection("12", "part / è")');
  assert.equal(app.run("busy"), true);
  assert.equal(app.el("chat-submit-btn").disabled, true);
  assert.equal(app.el("alert-box").textContent, "Existing alert");
  await app.run('updateTask({clear: true})');
  assert.equal(app.calls.length, 1);
  assert.equal(app.calls[0].path, "/api/section");
  assert.deepEqual(JSON.parse(app.calls[0].options.body), { node_id: 12, key: "part / è" });
  assert.equal(app.calls[0].options.headers["Content-Type"], "application/json");
  assert.equal(app.calls[0].options.method, "POST");
  complete({ ok: true, json: async () => ({ state: { revision: 3 } }) });
  await pending;
  assert.equal(app.renders[0].revision, 3);
  assert.equal(app.run("busy"), false);
  assert.equal(app.el("chat-submit-btn").disabled, false);

  app.context.respond = () => ({ ok: true, json: async () => ({ state: { revision: 4 } }) });
  await app.run('updateTask({goal: "Goal", constraints: ["one"], decisions: []})');
  assert.deepEqual(JSON.parse(app.calls[1].options.body), { goal: "Goal", constraints: ["one"], decisions: [] });
  assert.equal(app.renders[1].revision, 4);
});

test("task failures release controls and stopped actions never fetch", async () => {
  const app = cockpit();
  app.context.respond = () => ({ ok: false, status: 409, json: async () => ({ error: "Stale state" }) });
  await app.run('updateTask({clear: true})');
  assert.equal(app.calls[0].path, "/api/task");
  assert.deepEqual(JSON.parse(app.calls[0].options.body), { clear: true });
  assert.equal(app.el("alert-box").textContent, "Stale state");
  assert.equal(app.run("busy"), false);
  app.run("stopped = true");
  await app.run('openSection("1", "part")');
  await app.run("updateTask({clear: true})");
  assert.equal(app.calls.length, 1);
});

test("synaptic requests clear alerts, accept responses without state, and return null on failure", async () => {
  const app = cockpit();
  app.el("alert-box").textContent = "Old error";
  app.context.respond = () => ({ ok: true, json: async () => ({ candidates: [] }) });
  const result = await app.run('synapticRequest("/api/memory/search", {query: "test"})');
  assert.equal(result.candidates.length, 0);
  assert.equal(app.el("alert-box").textContent, "");
  assert.equal(app.renders.length, 0);
  app.context.respond = () => { throw new Error("Connection failed"); };
  assert.equal(await app.run('synapticRequest("/api/maintenance/preview", {node_id: 1})'), null);
  assert.equal(app.el("alert-box").textContent, "Connection failed");
  assert.equal(app.run("busy"), false);
});

test("chat, reset, recall, alternatives, and shutdown retain endpoint-specific effects", async () => {
  const app = cockpit();
  app.context.respond = () => ({ ok: true, json: async () => ({
    reply: { text: "Reply", trace: [1, 2] }, state: { status: "ready" },
  }) });
  await app.run('sendChat("Hello")');
  assert.equal(app.run("messages[0].role"), "Christian");
  assert.equal(app.run("messages[1].trace"), "1 → 2");
  await app.run("resetSession()");
  assert.equal(app.run("messages.length"), 1);
  assert.equal(app.run("messages[0].trace"), "");
  await app.run('recallNode("7")');
  await app.run('recallNode("8", true)');
  app.run("busy = true");
  await app.run("shutdownServer()");
  assert.equal(app.run("stopped"), true);
  assert.equal(app.el("alert-box").className, "notice success");
  assert.deepEqual(app.calls.map(call => [call.path, JSON.parse(call.options.body)]), [
    ["/api/chat", { text: "Hello" }], ["/api/reset", {}],
    ["/api/recall", { node_id: 7 }], ["/api/alternative", { node_id: 8 }],
    ["/api/shutdown", {}],
  ]);
});

test("individual and bulk navigation keep aria, content, and icons synchronized", () => {
  const app = cockpit();
  const button = element();
  const items = element();
  const icon = element();
  button.parentElement = { querySelector: () => items };
  button.querySelector = () => icon;
  const bare = element();
  bare.parentElement = element();
  app.groups.push(button, bare);
  app.run("bindEvents()");
  const check = expanded => {
    assert.equal(button.getAttribute("aria-expanded"), String(expanded));
    assert.equal(items.style.display, expanded ? "grid" : "none");
    assert.equal(icon.textContent, expanded ? "−" : "+");
  };
  button.listeners.click(); check(true);
  button.listeners.click(); check(false);
  app.el("expand-all-groups").listeners.click(); check(true);
  assert.equal(bare.getAttribute("aria-expanded"), "true");
  app.el("collapse-all-groups").listeners.click(); check(false);
  // Groups with no optional content/icon must still update accessibility state.
  bare.listeners.click();
  assert.equal(bare.getAttribute("aria-expanded"), "true");
});

test("page switching preserves display modes and ignores unknown pages", () => {
  const app = cockpit();
  for (const selected of ["memory", "graphs", "operational", "chat"]) {
    app.run(`switchPage(${JSON.stringify(selected)})`);
    for (const page of ["chat", "memory", "graphs", "operational"]) {
      assert.equal(app.el(`view-${page}`).style.display,
        page === selected ? (page === "chat" ? "grid" : "block") : "none");
    }
    assert.equal(app.run("currentPage"), selected);
  }
  const title = app.el("page-title").textContent;
  app.run('switchPage("unknown")');
  assert.equal(app.run("currentPage"), "chat");
  assert.equal(app.el("page-title").textContent, title);
});

test("maintenance preview IDs are invalidated on retry and consumed only after confirmed success", async () => {
  const app = cockpit();
  app.run("bindEvents()");
  app.el("maintenance-node").value = "42";
  app.context.respond = () => ({ ok: true, json: async () => ({ plan_id: "plan-1", plan: { groups: [1] } }) });
  const submit = () => app.el("maintenance-form").listeners.submit({ preventDefault() {} });
  await submit();
  assert.equal(app.run("pendingMaintenance"), "plan-1");
  assert.equal(app.el("maintenance-apply").disabled, false);
  app.context.window.confirm = () => false;
  await app.el("maintenance-apply").listeners.click();
  assert.equal(app.calls.length, 1);
  assert.equal(app.run("pendingMaintenance"), "plan-1");
  app.context.window.confirm = () => true;
  app.context.respond = () => ({ ok: true, json: async () => ({ operation_id: 9 }) });
  await app.el("maintenance-apply").listeners.click();
  assert.deepEqual(JSON.parse(app.calls[1].options.body), { plan_id: "plan-1", confirmed: true });
  assert.equal(app.run("pendingMaintenance"), null);
  assert.equal(app.el("maintenance-apply").disabled, true);
  assert.match(app.el("maintenance-preview").textContent, /#9/);
  app.run('pendingMaintenance = "stale"');
  app.context.respond = () => { throw new Error("Offline"); };
  await submit();
  assert.equal(app.run("pendingMaintenance"), null);
  assert.equal(app.el("maintenance-apply").disabled, true);
});

test("startup greets once and polling respects visibility, actions, and page teardown", async () => {
  const app = cockpit();
  app.context.respond = () => ({ ok: true, json: async () => ({ reply: { text: "Hi" }, state: { status: "ready" } }) });
  assert.equal(app.document.listeners.DOMContentLoaded, app.context.init);
  await app.run("init()");
  assert.deepEqual(app.calls.map(call => call.path), ["/api/state", "/api/chat"]);
  assert.equal(app.calls[1].options.body, '{"text":"Ciao"}');
  assert.equal(app.timers[0].delay, 5000);
  const poll = app.timers[0].callback;
  app.document.hidden = true;
  await poll();
  app.document.hidden = false;
  app.run("busy = true");
  await poll();
  app.run("busy = false; stopped = true");
  await poll();
  assert.equal(app.calls.length, 2);
  app.run("stopped = false");
  let complete;
  app.context.respond = () => new Promise(resolve => { complete = resolve; });
  const pending = poll();
  const rendered = app.renders.length;
  app.run("busy = true");
  complete({ ok: true, json: async () => ({ status: "ready" }) });
  await pending;
  assert.equal(app.renders.length, rendered);
  app.run("busy = false");
  app.context.respond = () => { throw new Error("Offline"); };
  await poll();
  assert.equal(app.el("alert-box").textContent, "");
  app.context.window.listeners.pagehide();
  assert.deepEqual(app.cleared, [1]);
});
