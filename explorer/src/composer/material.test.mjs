// Material editor pins (issue #82, docs/scope-composer.md task 4):
// list parsing per field kind + list edits through compile.
import { describe, it, expect } from "vitest";
import { readFile } from "node:fs/promises";
import { parseList } from "./main.jsx";
import { docToGraph, compile } from "./graph.mjs";
import { validateDocument } from "../validate.js";

const full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));

describe("parseList", () => {
  it("pitches: accepts SPN tokens, rejects non-pitches", () => {
    expect(parseList("D4 F#3 Bb5 C-1", "pitches")).toEqual({ value: ["D4", "F#3", "Bb5", "C-1"] });
    expect(parseList("D4 banana A4", "pitches").error).toContain("banana");
    expect(parseList("42", "pitches").error).toBeTruthy();
    expect(parseList("c4", "pitches").error).toBeTruthy();
  });
  it("numbers (durations): positive only", () => {
    expect(parseList("0.5 1 2.5", "numbers")).toEqual({ value: [0.5, 1, 2.5] });
    expect(parseList("0 1", "numbers").error).toBeTruthy();
    expect(parseList("-1 2", "numbers").error).toBeTruthy();
    expect(parseList("one", "numbers").error).toBeTruthy();
  });
  it("pattern: zero allowed (rests), negative rejected", () => {
    expect(parseList("1 0 0.75 0.25", "pattern")).toEqual({ value: [1, 0, 0.75, 0.25] });
    expect(parseList("1 -0.5", "pattern").error).toBeTruthy();
  });
  it("chords: free text passes through", () => {
    expect(parseList("Dm7 G7 Cmaj7 Bbmaj7", "chords")).toEqual({ value: ["Dm7", "G7", "Cmaj7", "Bbmaj7"] });
  });
  it("empty input parses to empty list", () => {
    expect(parseList("   ", "pitches")).toEqual({ value: [] });
  });
});

describe("material edits through compile", () => {
  it("motif pitch edit recompiles and validates", () => {
    const graph = docToGraph(full);
    const motif = graph.nodes.find((n) => n.kind === "motif" && n.key === "motif.a");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === motif.id ? { ...n, fields: { ...n.fields, pitches: ["E4", "G4", "B4"] } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    expect(out.material.motifs.find((m) => m.id === "motif.a").pitches).toEqual(["E4", "G4", "B4"]);
    expect(validateDocument(out)).toEqual([]);
  });

  it("progression chord edit recompiles and validates", () => {
    const graph = docToGraph(full);
    const prog = graph.nodes.find((n) => n.kind === "progression" && n.key === "prog.verse");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === prog.id ? { ...n, fields: { ...n.fields, chords: ["Em7", "A7"] } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    expect(out.material.harmony.progressions.find((p) => p.id === "prog.verse").chords).toEqual(["Em7", "A7"]);
    expect(validateDocument(out)).toEqual([]);
  });

  it("rhythm pattern edit recompiles and validates", () => {
    const graph = docToGraph(full);
    const rhythm = graph.nodes.find((n) => n.kind === "rhythm");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === rhythm.id ? { ...n, fields: { ...n.fields, pattern: [1, 0, 1, 0] } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    expect(out.material.rhythms[0].pattern).toEqual([1, 0, 1, 0]);
    expect(validateDocument(out)).toEqual([]);
  });

  it("out-of-register pitch edits validate structurally (register is semantic, not ajv)", () => {
    const graph = docToGraph(full);
    const motif = graph.nodes.find((n) => n.kind === "motif" && n.key === "motif.a");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === motif.id ? { ...n, fields: { ...n.fields, pitches: ["C8"] } } : n)),
      edges: graph.edges,
    };
    // theme.1 register bound is [C4, A5]; C8 parses as a pitch and the
    // register constraint is not cross-checked by ajv — pin the boundary so
    // a future semantic register check lands deliberately.
    const out = compile(edited, full);
    expect(validateDocument(out)).toEqual([]);
  });

  it("clearing a motif's pitches entirely is schema-legal (info, not error)", () => {
    const graph = docToGraph(full);
    const motif = graph.nodes.find((n) => n.kind === "motif" && n.key === "motif.a");
    const edited = {
      nodes: graph.nodes.map((n) => (n.id === motif.id ? { ...n, fields: { ...n.fields, pitches: [] } } : n)),
      edges: graph.edges,
    };
    const out = compile(edited, full);
    // Schema allows empty arrays — the composer surfaces this as info, not
    // an error (benchmark recall would degrade to unfound downstream).
    expect(validateDocument(out)).toEqual([]);
    expect(out.material.motifs.find((m) => m.id === "motif.a").pitches).toEqual([]);
  });
});
