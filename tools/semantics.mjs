// Semantic document checks — constraints JSON Schema cannot express in draft
// 2020-12 (no cross-value comparison, no cross-field logic). Same class as the
// harness's cross-reference lint; kept in code. Extend here as more semantic
// rules get pinned (they belong in one place, not scattered across test files).

// tempo.range must satisfy min <= max.
const orderedRanges = (doc) => !doc?.tempo?.range || doc.tempo.range[0] <= doc.tempo.range[1];

// Returns human-readable errors; empty means the doc is consistent.
export const checkSemantics = (doc) => {
  const errors = [];
  if (doc?.globals && !orderedRanges(doc.globals)) {
    errors.push(`globals.tempo.range inverted: [${doc.globals.tempo.range.join(", ")}]`);
  }
  return errors;
};
