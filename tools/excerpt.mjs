// --bars excerpt derivation (issue #120): truncate the form to the first
// sections totaling ≥ N bars AND prune constraint references that would be
// unwinnable by construction — the excerpt is a coherent document, not a
// form with dangling obligations. Harmony binds per form section
// (form.sections[].harmony → spans), so it follows the truncation on its
// own; motifs are global (material.motifs), so must_contain is untouched.
// What needs pruning: constraints.tempo_shapes keys (metrics fail any
// shape whose section left the form — a hard failure by design, the typo
// detector for real documents) and form.repetition (min/max clamp to the
// occurrences the truncated order actually keeps; entries below the
// clamped floor are dropped).
export const excerptDoc = (doc, maxBars) => {
  const d = JSON.parse(JSON.stringify(doc));
  const origCounts = new Map();
  for (const id of d.form?.order ?? []) origCounts.set(id, (origCounts.get(id) ?? 0) + 1);
  const kept = [];
  let bars = 0;
  for (const id of d.form?.order ?? []) {
    if (bars >= maxBars) break;
    kept.push(id);
    bars += d.form?.sections?.find((s) => s.id === id)?.bars ?? 4;
  }
  d.form ??= {};
  d.form.order = kept;
  const keptCounts = new Map();
  for (const id of kept) keptCounts.set(id, (keptCounts.get(id) ?? 0) + 1);

  if (d.form.repetition) {
    for (const [id, r] of Object.entries(d.form.repetition)) {
      const k = keptCounts.get(id) ?? 0;
      if (k === 0) delete d.form.repetition[id];
      else if (k < (origCounts.get(id) ?? k)) {
        if (r.min != null) r.min = Math.min(r.min, k);
        if (r.max != null) r.max = Math.max(r.min ?? 1, Math.min(r.max, k));
      }
    }
    if (Object.keys(d.form.repetition).length === 0) delete d.form.repetition;
  }
  if (d.constraints?.tempo_shapes) {
    for (const id of Object.keys(d.constraints.tempo_shapes))
      if (!keptCounts.has(id)) delete d.constraints.tempo_shapes[id];
    if (Object.keys(d.constraints.tempo_shapes).length === 0) delete d.constraints.tempo_shapes;
  }
  return d;
};
