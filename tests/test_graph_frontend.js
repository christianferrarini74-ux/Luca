/* Pure display tests run with the existing Node runtime, not an app dependency. */
"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {projectGraph, layoutGraph, traversedEdges, fitCamera, MemoryGraph, matchingRepresentatives} = require("../luca_memory/web/graph.js");
const snapshot = {
  nodes:[{id:1,root_id:1,title:"Same",part_count:1}, {id:2,root_id:1,title:"Part"},
         {id:3,root_id:3,title:"Same"}, {id:4,root_id:4,title:"Isolated"}],
  edges:[{source:1,target:2},{source:1,target:3},{source:3,target:1},{source:4,target:4}]
};
test("collapsed families preserve external directions without invented links", () => {
  const model = projectGraph(snapshot);
  assert.deepEqual(model.nodes.map(n => n.id), [1,3,4]);
  assert.deepEqual(model.edges.map(e => [e.source,e.target]), [[1,3],[3,1],[4,4]]);
  assert.equal(model.representative(2), 1);
});
test("expansion restores the real star and leaves duplicate titles independent", () => {
  const model = projectGraph(snapshot, new Set([1]));
  assert.equal(model.nodes.length, 4);
  assert.equal(model.edges.length, 4);
  assert.equal(model.edges[0].family, true);
  assert.equal(model.representative(2), 2);
  assert.equal(snapshot.nodes.length, 4);
});
test("partial families remain visible when the parent is outside the snapshot", () => {
  const model = projectGraph({nodes:[snapshot.nodes[1]],edges:[]});
  assert.equal(model.nodes[0].id, 2);
});
test("traversal uses canonical family identity and never turns a global entry into an edge", () => {
  const routes = traversedEdges({...snapshot, navigation:[
    {action:"open", source:"local", reading_id:2, target_id:3},
    {action:"open", source:"global", reading_id:3, target_id:4}
  ]});
  assert.deepEqual([...routes], ["1:3"]);
});
test("layout handles empty, self-linked, and larger graphs with finite coordinates", () => {
  assert.equal(layoutGraph([], []).size, 0);
  const nodes = Array.from({length:500}, (_,i) => ({id:i}));
  const points = layoutGraph(nodes, [{source:1,target:1}]);
  assert.equal(points.size, 500);
  for (const point of points.values()) assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y));
});
test("changing scope after dragging copies browser DOMPoint coordinates, not enumerable fields", () => {
  // DOMPoint exposes x/y on its prototype, so object spread loses them.
  const browserPoint = Object.create({get x() {return -900;}, get y() {return 130;}});
  assert.deepEqual({...browserPoint}, {});
  const points = layoutGraph(snapshot.nodes, snapshot.edges, new Map([[1, browserPoint]]));
  for (const point of points.values()) assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y));
});
test("invalid saved positions cannot poison the next layout", () => {
  const points = layoutGraph(snapshot.nodes, snapshot.edges, new Map([[1, {x:NaN,y:Infinity}]]));
  for (const point of points.values()) assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y));
});
test("fit centers a lone negative-coordinate node in wide and narrow viewports", () => {
  for (const [width,height] of [[1158,600],[320,470],[1800,600]]) {
    const c = fitCamera([{x:-1200,y:-950}], width, height);
    assert.equal(c.x + c.w/2, -1200);
    assert.equal(c.y + c.h/2, -950);
    assert.equal(c.w/c.h, width/height);
  }
});
test("fit includes negative/extreme bounds with pixel padding and handles empty/bad geometry", () => {
  const points = [{x:-2400,y:-800},{x:1800,y:1200}];
  const c = fitCamera(points, 1200, 600);
  for (const p of points) {
    const x = (p.x-c.x)/c.w*1200, y = (p.y-c.y)/c.h*600;
    assert.ok(x >= 119 && x <= 1081 && y >= 79 && y <= 521);
  }
  assert.deepEqual(fitCamera([{x:NaN,y:NaN}],0,0), {x:-400,y:-300,w:800,h:600});
});
test("fit recovers a corrupted map and ignores positions outside the current scope", () => {
  const graph = {model:{nodes:[{id:1}],edges:[]}, positions:new Map([[1,{x:NaN,y:NaN}],[999,{x:1e8,y:1e8}]]),
    svg:{clientWidth:1200,clientHeight:600}, drag:{id:1}, draw() {this.drawn = true;}};
  MemoryGraph.prototype.fit.call(graph);
  assert.equal(graph.drag, null);
  assert.ok(graph.drawn);
  assert.equal(graph.positions.size,1);
  const point = graph.positions.get(1);
  assert.equal(graph.camera.x + graph.camera.w/2,point.x);
});
test("search indexes collapsed child titles once and respects family expansion", () => {
  let model = projectGraph(snapshot);
  assert.deepEqual([...matchingRepresentatives(snapshot, model.representative, "part")], [1]);
  assert.deepEqual([...matchingRepresentatives(snapshot, model.representative, "same")], [1,3]);
  assert.equal(matchingRepresentatives(snapshot, model.representative, ""), null);
  model = projectGraph(snapshot, new Set([1]));
  assert.deepEqual([...matchingRepresentatives(snapshot, model.representative, "part")], [2]);
  assert.deepEqual([...matchingRepresentatives(snapshot, model.representative, "unknown")], []);
});
