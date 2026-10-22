# Fix: centering after dragging

2026-10-22. [Italiano](it/fase-1-sinapsi/19-correzione-centratura-mappa.md).

The reported page had `translate(NaN,NaN)` on every node and four `NaN` values
in the SVG viewBox. Switching views or fitting could not recover the geometry.

Dragging stored a browser `DOMPoint`. The next layout copied it with object
spread, but its coordinates are prototype properties, not enumerable fields.
The copy lost x/y, poisoning the layout. A regression using non-enumerable
getters failed before the fix.

Dragging now stores plain numeric coordinates. Layout explicitly copies x/y
and replaces non-finite positions. Fit rebuilds corrupted geometry, considers
only current-view nodes, cancels pending dragging and centers the bounds using
the actual viewport aspect ratio and pixel padding for labels/hit targets.
The viewBox also guards against invalid dimensions.

Validation: **10 JavaScript tests**, covering drag→scope changes, invalid
coordinates, a single negative-coordinate node, narrow/wide viewports and
corrupted-map recovery. **219 Python tests passed** with real CUDA/tokenizer
enabled and no skips. Browser checks on disposable storage included a real
drag, completed global→focus transitions, fit, and DOM verification that all
three nodes were inside the canvas with finite coordinates. Screenshot:
`D:\Test\Luca\memory-graph-fit-20261022.png`.

No memory, API, model or dependency changes. The user's existing page was
inspected without reloading it, sending chat or changing Core focus. Reload
the page (Ctrl+F5) to load the fixed script; no server restart is needed.
The current frontend reinitializes its visible transcript and sends an initial
greeting on load; do not use New Session for this fix. The separate test server
is closed after verification.
