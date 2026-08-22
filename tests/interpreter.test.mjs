// Tests for interpreter/expand.mjs (issue #23, per docs/scope-batch3.md).
// No live model calls: callModel is injected (fake model path); wire
// adapters are env-configured for real use only.
// Standalone runner: `node tests/interpreter.test.mjs`; also folded into npm test.
import { readFile } from "node:fs/promises";
import { expand, buildPrompt, parseModelOutput, summarizeConstraints, defaultModelConfig } from "../interpreter/expand.mjs";

const minimal = JSON.parse(await readFile(new URL("../examples/minimal.muse.json", import.meta.url), "utf8"));
const full = JSON.parse(await readFile(new URL("../examples/full.muse.json", import.meta.url), "utf8"));
const fakePerf = JSON.parse(await readFile(new URL("../interpreter/fixtures/minimal-expansion.muse.perf.json", import.meta.url), "utf8"));
const fakeJson = JSON.stringify(fakePerf);

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); }
};

// DoD: minimal.muse.json expands to a validating performance document via
// the (fake) model path. The harness re-validates the fixture on every run,
// so fixture rot fails here.
{
  const { perf, attempts } = await expand({
    doc: minimal,
    callModel: async () => fakeJson,
    model: "fake-model-v0",
    at: "2026-08-22T12:00:00Z",
  });
  check("minimal.muse.json expands to a validating perf doc", !!perf && attempts === 1);
  check("provenance stamped by harness, not the model",
    perf.metadata.interpreter.model === "fake-model-v0" && perf.metadata.interpreter.at === "2026-08-22T12:00:00Z");
  check("source rendition resolved from document", perf.metadata.source.rendition_id === "r.default");
}

// DoD: invalid model output is caught and retried, not silently accepted.
{
  const calls = [];
  const script = [
    "not json at all",                                   // unparseable
    JSON.stringify({ ...fakePerf, notes: [{ ...fakePerf.notes[0], part: "p.ghost" }] }), // dangling ref
    fakeJson,                                            // valid
  ];
  const { perf, attempts } = await expand({
    doc: minimal,
    callModel: async (prompt, { attempt }) => { calls.push(prompt); return script[attempt - 1]; },
    model: "fake-model-v0",
    at: "2026-08-22T12:00:00Z",
  });
  check("invalid outputs retried until valid", attempts === 3 && !!perf);
  check("retry carries validation feedback to the model",
    calls.length === 3 && calls[1].user.includes("previous attempt failed validation")
    && calls[2].user.includes("p.ghost"));
}

// Fail loudly after bounded attempts.
{
  let err = null;
  try {
    await expand({ doc: minimal, callModel: async () => "[]", model: "fake", maxAttempts: 2 });
  } catch (e) { err = e; }
  check("fails loudly after maxAttempts with validation errors",
    err !== null && err.message.includes("2 attempts") && Array.isArray(err.validationErrors) && err.validationErrors.length > 0);
}

// Constraint semantics pass (issue #90): the retry loop feeds the
// conformance metrics — a performance that drops a must_contain motif
// fails with the metric's error detail, and the feedback reaches the model.
{
  const constrained = {
    ...minimal,
    material: { motifs: [{ id: "motif.a", kind: "pitch_rhythm", pitches: ["D4", "F4", "A4"], durations: [1, 1, 1] }] },
    constraints: { must_contain: ["motif.a"] },
  };
  const calls = [];
  const script = [
    fakeJson,           // fixture has C-E-G, not the D-F-A motif → metric failure
    JSON.stringify({ ...fakePerf, notes: [
      { part: "p1", pitch: 62, pitch_name: "D4", onset: 0, duration: 0.625, onset_beat: 0, duration_beats: 1, velocity: 80 },
      { part: "p1", pitch: 65, pitch_name: "F4", onset: 0.625, duration: 0.625, onset_beat: 1, duration_beats: 1, velocity: 80 },
      { part: "p1", pitch: 69, pitch_name: "A4", onset: 1.25, duration: 0.625, onset_beat: 2, duration_beats: 1, velocity: 80 },
    ] }),
  ];
  const { perf, attempts } = await expand({
    doc: constrained,
    callModel: async (prompt, { attempt }) => { calls.push(prompt); return script[attempt - 1]; },
    model: "fake-model-v0",
    at: "2026-08-22T12:00:00Z",
  });
  check("dropped must_contain motif fails with metric error and retries",
    attempts === 2 && !!perf);
  check("metric error detail reaches the model on retry",
    calls.length === 2 && calls[1].user.includes("motif_recall") && calls[1].user.includes("motif.a"));
}

// Rendition resolution.
{
  let err = null;
  try { await expand({ doc: full, callModel: async () => fakeJson, model: "fake" }); }
  catch (e) { err = e; }
  check("ambiguous rendition (multiple, none picked) errors", err !== null && err.message.includes("r.synthwave"));
}
{
  let err = null;
  try { await expand({ doc: full, renditionId: "r.ghost", callModel: async () => fakeJson, model: "fake" }); }
  catch (e) { err = e; }
  check("unknown rendition id errors", err !== null && err.message.includes("r.ghost"));
}

// Prompt contents: schema + rendition + perf schema + instructions.
{
  const prompt = buildPrompt({ doc: minimal, rendition: { id: "r.default" }, perfSchema: { type: "object" }, constraintSummary: summarizeConstraints(minimal) });
  const payload = JSON.parse(prompt.user);
  check("prompt carries document, rendition, perf schema, constraint summary",
    !!payload.muse_document && payload.active_rendition.id === "r.default"
    && !!payload.performance_schema && !!payload.constraint_summary);
  check("prompt instructions demand JSON-only output", prompt.system.includes("ONLY the performance document"));
}

// parseModelOutput: fences tolerated, prose rejected.
check("fenced JSON parses", parseModelOutput("```json\n{\"a\":1}\n```").a === 1);
{
  let ok = false;
  try { parseModelOutput("Here is your document: {\"a\":1}"); } catch { ok = true; }
  check("prose-wrapped output rejected", ok);
}

// Env config: no hard-coded model/key defaults.
check("missing MUSE_MODEL errors", (() => { try { defaultModelConfig({}); return false; } catch { return true; } })());
check("missing provider key errors", (() => { try { defaultModelConfig({ MUSE_MODEL: "x", MUSE_PROVIDER: "anthropic" }); return false; } catch { return true; } })());
check("unknown provider errors", (() => { try { defaultModelConfig({ MUSE_MODEL: "x", MUSE_PROVIDER: "bogus", BOGUS_API_KEY: "k" }); return false; } catch { return true; } })());
check("openai config resolves with base-url override",
  defaultModelConfig({ MUSE_MODEL: "gpt-x", MUSE_PROVIDER: "openai", OPENAI_API_KEY: "k", MUSE_BASE_URL: "http://localhost:1" }).model === "gpt-x");

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
