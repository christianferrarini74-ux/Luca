# Interactive memory graph

> **Historical record — not current operating instructions.** Designs, defaults, results and next steps below belong to the recorded milestone. For current scope, APIs and behavior read the [current contract](memory-integration-contract.md). Original evidence is preserved.

Date: 2026-10-22. [Italiano](it/fase-1-sinapsi/18-mappa-grafica-memoria.md).

## Scope and controls

The cockpit now includes **Memoria & Sinapsi → Mappa della memoria**. It replaces
the row-based graph that inferred links through titles and recalled nodes on
click. The SVG map uses V1 knowledge-catalog IDs and actual directed SQLite edges.

- **Globale**: overview within configured display limits.
- **Focus · primo grado**: the focus family and directly adjacent families,
  including incoming/outgoing connections. Empty when there is no focus.
- **Esplora vicinato**: changes only the inspected center, not Luca's focus.
  The banner distinguishes inspection center from actual focus/reading IDs.
- Click or Enter/Space selects metadata without reading node contents.
- Expand/collapse restores or hides the A–An family star. External edges stay
  on the parent. Colors describe individual nodes, not an invented family-wide
  residency; the inspector also counts included family members by tier.
- Drag nodes/background; use the wheel, zoom buttons and fit control.
- **Cerca nella vista** highlights included IDs/titles, including collapsed
  family members; it does not search document contents or excluded nodes.
- **Richiama nella giostra** is the only map action requesting a real focus
  change from the Core; it is disabled while an operation is running.

Green means VRAM, amber RAM, grey SSD as the highest currently occupied tier;
SSD still retains persistent data. Host mode explicitly warns that the VRAM
tier is not physical GPU memory. Blue marks focus and purple marks a turn's
read node. Traversed local routes highlight existing edges, including reverse
traversal; global entries are listed without inventing links. The list describes
the navigator's latest turn, not persistent movement history.

## Engine boundary and limits

`GET /api/graph?mode=global` returns metadata; `mode=focus` inspects the current
focus neighborhood, optionally centered on `node_id=123`. Invalid queries return
400; unknown IDs return 404. It uses the lock shared with Core mutations without
recalling nodes, reading cell bodies, changing events/counters or resetting the
idle timer. Existing cockpit APIs with content excerpts remain unchanged.

`graph_view.py` builds the snapshot; `web/graph.js` owns only layout, selection
and interactions. Visual distances are not semantic similarity or reasoning.
No memory/model policy moved into the GUI. No new Python/JavaScript dependency,
CDN, service or Node process is required: start with `python run_luca.py`.

```yaml
frontend:
  enabled: true
  graph:
    node_limit: 500
    edge_limit: 2000
```

These limit display, not memory. Accepted ranges: 1–2000 nodes, 1–10000 edges.
The center is prioritized, then IDs are ordered; only edges between included
nodes are returned, within the cap. Counts and partial-view warnings are explicit.
Complete pagination and graph-wide search beyond the caps are not implemented;
large libraries need further validation. Low caps may yield incomplete families.

## Verification and handoff

**219 Python tests passed**, with no skips and real LM Studio tokenization/CUDA
enabled; **5 JavaScript tests passed** using the existing Node runtime for tests
only. Coverage includes duplicate titles/IDs, direction, families, partial views,
limits, HTTP errors, no cell-body reads, unchanged focus/revisions/events/tiers.
A real-CUDA test checks residency and unchanged transfer counters before/after.

```powershell
$env:LUCA_TEST_CUDA='1'
$env:LUCA_TEST_LMSTUDIO='1'
.venv/Scripts/python.exe -m unittest discover -s tests
node --test tests/test_graph_frontend.js
```

Browser checks used a separate server with in-memory SQLite: global/local views,
keyboard selection, family expansion, search, zoom/fit, explicit recall, light
and dark themes. Dark-theme contrast was corrected during verification.
Local screenshot: `D:\Test\Luca\memory-graph-20261022.png` (synthetic data, host backend).

The test server is closed after verification. Personal memory and the user's
running Luca instance are not modified or restarted. To load the new API, stop
the old instance cleanly with **Arresta Luca**, then run `python run_luca.py` and
open the new navigation item. No package reinstall is needed.
