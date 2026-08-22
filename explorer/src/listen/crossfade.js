// A/B rendition crossfade (docs/scope-listener.md, task 3): two renditions
// of the same schema pre-rendered; switching crossfades at the current
// playback position. Position continuity comes from the form — both
// renditions share the section/bar structure, so a bar position in A maps
// to the same bar position in B even when the tempos differ.
// Pure math, no AudioContext — the Listen tab owns the plumbing.

// Position → bar position (fractional bars from piece start), honoring
// form repetition (min bounds, matching the offline expander's rule).
export const positionToBar = (doc, seconds, bpm) => {
  const meter = doc?.globals?.meter;
  const beatsPerBar = meter
    ? (Array.isArray(meter.beats) ? meter.beats.reduce((a, b) => a + b, 0) : meter.beats) * (4 / (meter.unit ?? 4))
    : 4;
  return (seconds * (bpm ?? 96)) / 60 / beatsPerBar;
};

export const barToPosition = (doc, bar, bpm) => {
  const meter = doc?.globals?.meter;
  const beatsPerBar = meter
    ? (Array.isArray(meter.beats) ? meter.beats.reduce((a, b) => a + b, 0) : meter.beats) * (4 / (meter.unit ?? 4))
    : 4;
  return (bar * beatsPerBar * 60) / (bpm ?? 96);
};

// Equal-power crossfade gains at progress t ∈ [0,1]: A fades cos, B fades
// sin so total power stays constant.
export const crossfadeGains = (t) => {
  const clamped = Math.max(0, Math.min(1, t));
  return [Math.cos((clamped * Math.PI) / 2), Math.sin((clamped * Math.PI) / 2)];
};

// A crossfade plan: given the source transport position, the shared doc,
// and both renditions' tempos, where in B does the switch land?
export const planSwitch = (doc, positionSeconds, fromBpm, toBpm) => {
  const bar = positionToBar(doc, positionSeconds, fromBpm);
  return { bar, targetSeconds: barToPosition(doc, bar, toBpm) };
};
