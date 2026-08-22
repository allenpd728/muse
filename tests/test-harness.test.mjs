// Unit tests for tools/test.mjs danglingRefs() — issue #27, per
// tests/open_20260822-013951_test-harness.md.
// Standalone runner: `node tests/test-harness.test.mjs`; also folded into npm test.
import { danglingRefs } from "../tools/test.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};
const dangles = (doc) => danglingRefs(doc).map((d) => d.ref);

const material = {
  motifs: [{ id: "motif.a" }],
  themes: [{ id: "theme.1" }],
  rhythms: [{ id: "groove.1" }],
  harmony: { progressions: [{ id: "prog.verse" }] },
};

// uses[].ref resolution + transform suffix stripping
check("uses ref to motif/theme/rhythm ids resolve", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ ref: "motif.a" }, { ref: "theme.1" }, { ref: "groove.1" }] }] },
}).length === 0);
check("transform-suffixed ref strips to base id", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ ref: "motif.a#seq(+2)" }, { ref: "motif.a#inv" }] }] },
}).length === 0);
check("multi-# ref: base id is first segment", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ ref: "motif.a#inv#seq(+2)" }] }] },
}).length === 0);
check("unknown uses ref dangles", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ ref: "motif.missing" }] }] },
}).includes("motif.missing"));

// harmony refs resolve against progression ids only
check("section harmony ref to progression id resolves", dangles({
  material,
  form: { sections: [{ id: "s1", harmony: "prog.verse" }] },
}).length === 0);
check("harmony ref to a motif id dangles", dangles({
  material,
  form: { sections: [{ id: "s1", harmony: "motif.a" }] },
}).includes("motif.a"));
check("unknown harmony ref dangles", dangles({
  material,
  form: { sections: [{ id: "s1", harmony: "prog.missing" }] },
}).includes("prog.missing"));

// constraints.must_contain
check("must_contain resolves against material ids", dangles({
  material,
  constraints: { must_contain: ["motif.a", "theme.1", "groove.1"] },
}).length === 0);
check("must_contain unknown id dangles", dangles({
  material,
  constraints: { must_contain: ["motif.missing"] },
}).includes("motif.missing"));

// Missing sections: no crash, only present sections checked
check("doc with no material/form/constraints: no dangles, no crash", dangles({ muse_version: "0.1" }).length === 0);
check("form without material: uses refs dangle", dangles({
  form: { sections: [{ id: "s1", uses: [{ ref: "motif.a" }] }] },
}).includes("motif.a"));

// Sparse entries skipped, not flagged
check("material entries without id skipped", dangles({
  material: { motifs: [{ kind: "pitch" }] },
  form: { sections: [{ id: "s1" }] },
}).length === 0);
check("uses entry without ref skipped", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ variation: "plain" }] }] },
}).length === 0);
check("section without harmony skipped", dangles({
  material,
  form: { sections: [{ id: "s1" }] },
}).length === 0);
check("progressions without id do not crash", dangles({
  material: { harmony: { progressions: [{ chords: ["Dm7"] }] } },
  form: { sections: [{ id: "s1", harmony: "prog.verse" }] },
}).includes("prog.verse"));

// Edge cases
check("empty sections and must_contain: no dangles", dangles({
  material,
  form: { sections: [] },
  constraints: { must_contain: [] },
}).length === 0);

// --- Reference surfaces added in #47 ---
const withSections = {
  material,
  form: {
    sections: [{ id: "verse.1" }, { id: "chorus.1" }],
    order: ["verse.1", "chorus.1", "verse.1"],
    repetition: { "verse.1": { min: 2, max: 4 } },
  },
  constraints: {
    tempo_lock: { "chorus.1": [92, 104] },
    register: { "theme.1": ["C4", "A5"] },
  },
};
check("all five surfaces resolve when ids exist", dangles(withSections).length === 0);

check("theme phrase motif ref resolves against material ids", dangles({
  material,
  form: { sections: [{ id: "s1" }], order: ["s1"] },
}).length === 0);
check("theme phrase motif ref to unknown id dangles", dangles({
  material: { themes: [{ id: "theme.1", phrases: [{ motifs: ["motif.ghost"] }] }] },
  form: { sections: [{ id: "s1" }], order: ["s1"] },
}).includes("motif.ghost"));
check("theme phrase motif ref strips transform suffix", dangles({
  material: { ...material, themes: [{ id: "theme.1", phrases: [{ motifs: ["motif.a#inv"] }] }] },
  form: { sections: [{ id: "s1" }], order: ["s1"] },
}).length === 0);

check("form.order ghost section dangles", dangles({
  ...withSections,
  form: { ...withSections.form, order: ["verse.1", "section.ghost"] },
}).includes("section.ghost"));
check("form.repetition ghost key dangles", dangles({
  ...withSections,
  form: { ...withSections.form, repetition: { "section.ghost": { min: 1, max: 2 } } },
}).includes("section.ghost"));
check("constraints.tempo_lock ghost key dangles", dangles({
  ...withSections,
  constraints: { ...withSections.constraints, tempo_lock: { "section.ghost": [90, 100] } },
}).includes("section.ghost"));
check("constraints.register ghost material key dangles", dangles({
  ...withSections,
  constraints: { ...withSections.constraints, register: { "motif.ghost": ["C4", "A5"] } },
}).includes("motif.ghost"));
check("order/repetition/tempo_lock/register absent: no dangles, no crash", dangles({
  material,
  form: { sections: [{ id: "s1" }] },
}).length === 0);
check("pinned: harmony as object is flagged (form.schema.json types harmony as string; spec §2.5 cross-ref requires it to resolve)", dangles({
  material,
  form: { sections: [{ id: "s1", harmony: { ref: "prog.verse" } }] },
}).length === 1);
check("pinned: progression id as uses ref dangles (uses targets material ids; harmony progressions are referenced via section harmony only)", dangles({
  material,
  form: { sections: [{ id: "s1", uses: [{ ref: "prog.verse" }] }] },
}).includes("prog.verse"));

// --- Residual pins (issue #55, spec: tests/open_20260822-105836_crossref-surfaces.md) ---

// Kind-narrowing decision: pool convention stays. Phrase motifs[] and
// uses[].ref resolve against the full material id pool (motifs + themes +
// rhythms), even though the field description says "Motif references" —
// flagging kinds would be a new semantic rule, deliberately not bundled
// into #47.
check("pinned (pool convention): theme id in a phrase motifs[] position resolves", dangles({
  material: { themes: [{ id: "theme.1" }, { id: "theme.2", phrases: [{ motifs: ["theme.1"] }] }] },
  form: { sections: [{ id: "s1" }] },
}).length === 0);

// Duplicate section ids: sectionIds() is a Set, so a duped id resolves refs —
// the lint relies on form-semantic's "duplicate section ids" check
// (tests/form-semantic.test.mjs) to flag the document instead.
check("pinned: duplicate section ids make refs to that id resolve (dup check lives in form-semantic)", dangles({
  material,
  form: { sections: [{ id: "s1" }, { id: "s1" }], order: ["s1"] },
}).length === 0);

// baseRef on a non-string ref (schema-invalid doc): String() coercion means
// no crash; the ref resolves if the stringified value matches an id.
check("pinned: numeric uses ref does not crash and resolves when stringified id matches", dangles({
  material: { motifs: [{ id: "1" }] },
  form: { sections: [{ id: "s1", uses: [{ ref: 1 }] }] },
}).length === 0);

// register/tempo_lock keys are compared literally, never transform-stripped:
// a key containing "#" dangles unless an id literally contains it (ids are
// dotted slugs per §2.8, so "#" never appears).
check("pinned: register key containing # dangles (keys are not transform-stripped)", dangles({
  material,
  form: { sections: [{ id: "s1" }] },
  constraints: { register: { "motif.a#inv": ["C4", "A5"] } },
}).includes("motif.a#inv"));

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
