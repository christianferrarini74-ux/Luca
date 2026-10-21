/* Pure display tests run with the existing Node runtime, not an app dependency. */
"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const {projectGraph, layoutGraph, traversedEdges} = require("../luca_memory/web/graph.js");
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
