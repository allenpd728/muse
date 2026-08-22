// Semantic document checks — constraints JSON Schema cannot express in draft
// 2020-12 (no cross-value comparison, no cross-field logic). Same class as the
// harness's cross-reference lint; kept in code. Extend here as more semantic
// rules get pinned (they belong in one place, not scattered across test files).

// tempo.range must satisfy min <= max.
const orderedRanges = (doc) => !doc?.tempo?.range || doc.tempo.range[0] <= doc.tempo.range[1];

// §2.6 hard rule: style.references describe styles, eras, and production
// techniques — named-artist imitation is out of spec without an attached
// license record. Heuristic: "sounds like <name>" or "in the style of
// <name>" phrasing is a named-artist reference.
const ARTIST_REF_RE = /\b(sounds? like|in the style of)\b/i;

// Returns human-readable errors; empty means the doc is consistent.
export const checkSemantics = (doc) => {
  const errors = [];
  if (doc?.globals && !orderedRanges(doc.globals)) {
    errors.push(`globals.tempo.range inverted: [${doc.globals.tempo.range.join(", ")}]`);
  }
  for (const r of doc?.renditions ?? []) {
    for (const ref of r?.style?.references ?? []) {
      if (ARTIST_REF_RE.test(ref)) {
        errors.push(
          `renditions.${r.id ?? "?"}: style.references entry names an artist ("${ref}") — policy violation per spec §2.6 hard rule`
        );
      }
    }
  }
  return errors;
};

// Performance-document reference integrity (spec §7): notes[].part and
// dynamics[].part must resolve against parts[].id. Same class as the
// harness's danglingRefs lint — cross-value, not expressible in draft
// 2020-12. Returns human-readable errors; empty means consistent.
export const checkPerfRefs = (doc) => {
  const errors = [];
  const partIds = new Set((doc?.parts ?? []).map((p) => p?.id).filter(Boolean));
  for (const [i, n] of (doc?.notes ?? []).entries())
    if (n?.part && !partIds.has(n.part))
      errors.push(`notes[${i}].part: dangling ref "${n.part}"`);
  for (const [i, d] of (doc?.dynamics ?? []).entries())
    if (d?.part && !partIds.has(d.part))
      errors.push(`dynamics[${i}].part: dangling ref "${d.part}"`);
  return errors;
};

// Clock consistency (spec §7, "two clocks"): seconds must agree with beats
// under the tempo_map. Beats are converted to seconds via linear interpolation
// between map points (constant bpm within a segment). Tolerance 1e-3s absorbs
// float dust from the interpolation; a musically meaningful mismatch is far
// larger.
export const checkClockConsistency = (doc, { tolerance = 1e-3 } = {}) => {
  const errors = [];
  const map = doc?.tempo_map ?? [];
  if (!map.length) return errors;
  const sorted = [...map].sort((a, b) => a.time - b.time);
  const beatToTime = (beat) => {
    if (beat <= sorted[0].beat)
      return sorted[0].time - ((sorted[0].beat - beat) * 60) / sorted[0].bpm;
    for (let i = 1; i < sorted.length; i++) {
      const a = sorted[i - 1], b = sorted[i];
      if (beat <= b.beat) return a.time + ((beat - a.beat) * 60) / a.bpm;
    }
    const last = sorted[sorted.length - 1];
    return last.time + ((beat - last.beat) * 60) / last.bpm;
  };
  for (const [i, n] of (doc?.notes ?? []).entries()) {
    if (typeof n?.onset !== "number" || typeof n?.onset_beat !== "number") continue;
    const expected = beatToTime(n.onset_beat);
    if (Math.abs(n.onset - expected) > tolerance)
      errors.push(`notes[${i}]: onset ${n.onset}s disagrees with onset_beat ${n.onset_beat} (${expected.toFixed(4)}s under tempo_map)`);
    if (typeof n?.duration === "number" && typeof n?.duration_beats === "number") {
      const end = beatToTime(n.onset_beat + n.duration_beats);
      if (Math.abs(n.onset + n.duration - end) > tolerance)
        errors.push(`notes[${i}]: duration ${n.duration}s disagrees with duration_beats ${n.duration_beats}`);
    }
  }
  return errors;
};
