// Round-trip fixture test for the composer graph model (issue #79, per
// docs/scope-composer.md task 1): every examples/ + benchmark/corpus/ doc
// must survive doc → graph → doc losslessly.
import { describe, test, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { docToGraph, compile } from "./graph.mjs";

const readJson = (p) => JSON.parse(readFileSync(p, "utf8"));

const FILES = [
  ...readdirSync("public/examples").filter((f) => f.endsWith(".muse.json")).map((f) => `public/examples/${f}`),
  ...readdirSync("../benchmark/corpus").filter((f) => f.endsWith(".muse.json")).map((f) => `../benchmark/corpus/${f}`),
];

describe("composer graph round-trip", () => {
  test("corpus is present", () => {
    expect(FILES.length).toBeGreaterThan(2);
  });

  for (const f of FILES) {
    test(`${f} round-trips losslessly`, () => {
      const doc = readJson(f);
      const graph = docToGraph(doc);
      expect(graph.nodes.length).toBeGreaterThan(0);
      expect(compile(graph, doc)).toEqual(doc);
    });
  }

  test("graph exposes the expected node kinds and edge types on the full example", () => {
    const g = docToGraph(readJson("public/examples/full.muse.json"));
    const kinds = new Set(g.nodes.map((n) => n.kind));
    for (const k of ["motif", "theme", "rhythm", "progression", "section", "rendition", "globals", "constraints"])
      expect(kinds.has(k), `kind ${k}`).toBe(true);
    const types = new Set(g.edges.map((e) => e.type));
    for (const t of ["phrase-motif", "uses", "harmony", "order"])
      expect(types.has(t), `edge type ${t}`).toBe(true);
  });
});
