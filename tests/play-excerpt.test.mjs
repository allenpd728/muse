// Excerpt derivation + --bars winnability (issue #120, per
// tests/closed_20260822-223000_excerpt-pruning.md): the truncated excerpt is
// a coherent document — constraint references to dropped sections are
// pruned, repetition clamps to kept occurrences — and the offline end-to-end
// path completes with structure/tempo metrics winnable against the excerpt.
// Offline only; no live calls. Standalone runner; folded into npm test.
import { mkdtempSync, readFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { excerptDoc } from "../tools/excerpt.mjs";
import { expandOffline } from "../interpreter/offline.mjs";
import { scorePerformance } from "../benchmark/metrics.mjs";

let passed = 0, failed = 0;
const check = (name, cond, detail) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else { failed++; console.error(`FAIL ${name}`); if (detail) console.error(detail); }
};

const full = JSON.parse(readFileSync("examples/full.muse.json", "utf8"));

// --bars 12: drops bridge.cadenza (and chorus/verse repeats after the first
// needed); repetition clamps to the single kept occurrence; the cadenza's
// ritardando constraint is pruned; global constraints survive; source
// document untouched.
const e12 = excerptDoc(full, 12);
check("excerpt 12: order truncated to prefix", JSON.stringify(e12.form.order) === '["verse.1"]');
check("excerpt 12: repetition clamped to kept occurrences",
  e12.form.repetition?.["verse.1"]?.min === 1 && e12.form.repetition?.["verse.1"]?.max === 1);
check("excerpt 12: cadenza ritardando pruned (empty object dropped)",
  e12.constraints.tempo_shapes === undefined);
check("excerpt 12: global constraints survive",
  e12.constraints.tempo_lock !== undefined && e12.constraints.register !== undefined && e12.constraints.must_contain?.length > 0);
check("excerpt 12: source document not mutated",
  full.form.repetition["verse.1"].min === 2 && full.constraints.tempo_shapes["bridge.cadenza"] !== undefined);

// --bars 36: keeps verse+chorus+verse — both verse occurrences survive, so
// repetition stays declared at {2,4}; the cadenza shape is still pruned.
const e36 = excerptDoc(full, 36);
check("excerpt 36: prefix through second verse",
  JSON.stringify(e36.form.order) === '["verse.1","chorus.1","verse.1"]');
check("excerpt 36: fully-kept sections keep original repetition bounds",
  e36.form.repetition["verse.1"].min === 2 && e36.form.repetition["verse.1"].max === 4);

// The excerpt is winnable for the expander that consumes it: structure and
// tempo metrics score 1.0 against the pruned document — no dangling
// obligations (the --bars 12 live-run failure mode on #113).
{
  const perf = expandOffline(e12, { id: "r.synthwave", name: "x", params: {} });
  const report = scorePerformance(e12, perf);
  check("excerpt 12: structure_fidelity winnable (16 of [16,16] bars)",
    report.structure_fidelity === 1, JSON.stringify(report.structure));
  check("excerpt 12: tempo_shapes winnable (no dangling shapes)",
    report.tempo_shapes === 1);
}

// CLI end-to-end, offline path: --bars excerpt exits 0 through the
// refs/semantics guard seam (the excerpt must be lint-clean too).
{
  const dir = mkdtempSync(path.join(tmpdir(), "excerpt-test-"));
  const r = spawnSync(process.execPath, ["tools/play.mjs", "examples/full.muse.json", "r.synthwave", "--bars", "12", "--out", dir], { encoding: "utf8" });
  check("CLI --bars 12 exits 0 (offline, guard seam clean)", r.status === 0, r.stderr);
  check("CLI excerpt produced perf + WAV",
    readdirSync(dir).some((f) => f.endsWith(".muse.perf.json")) && readdirSync(dir).some((f) => f.endsWith(".wav")));
}

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
