// Listen tab (docs/scope-listener.md, task 2): pick a rendition, hear the
// piece. Offline expansion on selection (interpreter/offline.mjs — no LLM
// client-side in MVP), transport bar over the #97 playback core. Read-only:
// playback state is not document state.
import React from "react";
import { expandOffline } from "../../../interpreter/offline.mjs";
import { renderToBuffer, createTransport, resolveContext } from "./player.js";
import { planSwitch, crossfadeGains } from "./crossfade.js";

const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

// Current form section by bar position, derived from the form order.
const sectionAt = (doc, seconds, bpm) => {
  const sections = doc?.form?.sections ?? [];
  const order = doc?.form?.order ?? [];
  if (!sections.length || !order.length) return null;
  const beatsPerSecond = (bpm ?? doc.globals?.tempo?.bpm ?? 96) / 60;
  const beatsPerBar = doc.globals?.meter
    ? (Array.isArray(doc.globals.meter.beats) ? doc.globals.meter.beats.reduce((a, b) => a + b, 0) : doc.globals.meter.beats) * (4 / (doc.globals.meter.unit ?? 4))
    : 4;
  let barCursor = Math.floor((seconds * beatsPerSecond) / beatsPerBar);
  const barsById = Object.fromEntries(sections.map((s) => [s.id, s.bars ?? 8]));
  for (const id of order) {
    const bars = barsById[id] ?? 8;
    if (barCursor < bars) return id;
    barCursor -= bars;
  }
  return order[order.length - 1];
};

export default function ListenTab({ doc }) {
  const renditions = doc?.renditions ?? [];
  const [active, setActive] = React.useState(null);       // rendition id
  const [state, setState] = React.useState(null);         // transport state
  const [error, setError] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [fading, setFading] = React.useState(false);
  const ctxRef = React.useRef(null);
  const transportRef = React.useRef(null);
  const bufferRef = React.useRef(null);
  const buffersRef = React.useRef(new Map());   // rendition id → AudioBuffer (pre-rendered for A/B)
  const fadeRef = React.useRef(null);           // { gains: [GainNode, GainNode], timer }

  const stop = () => { transportRef.current?.stop(); };

  // Pre-render a rendition into the buffer cache (A/B switching must not
  // wait on expansion at switch time).
  const prerender = (ctx, rendition) => {
    if (buffersRef.current.has(rendition.id)) return buffersRef.current.get(rendition.id);
    const perf = expandOffline(doc, rendition);
    if (!(perf.notes?.length > 0)) throw new Error("expansion produced no notes — this document's material is too sparse for the offline interpreter (see #91)");
    const buffer = renderToBuffer(ctx, perf);
    buffersRef.current.set(rendition.id, buffer);
    return buffer;
  };

  const play = async (rendition) => {
    setError(null);
    stop();
    // Same rendition playing → toggle pause.
    if (active === rendition.id && transportRef.current) {
      const s = transportRef.current.state();
      s.playing ? transportRef.current.pause() : transportRef.current.play();
      return;
    }
    setLoading(true);
    try {
      ctxRef.current ??= resolveContext();
      const ctx = ctxRef.current;
      const buffer = prerender(ctx, rendition);
      bufferRef.current = buffer;
      transportRef.current = createTransport(buffer, ctx, { onstatechange: setState });
      setActive(rendition.id);
      transportRef.current.play();
    } catch (e) {
      setError(e.message);
      setActive(null);
    } finally {
      setLoading(false);
    }
  };

  // A/B switch (task 3): crossfade to the other rendition at the mapped
  // bar position. Both renditions pre-rendered; the switch never re-expands.
  // The crossfade is a timed gain ramp on the outgoing transport (the
  // incoming one starts quiet and ramps up via the same timers) — the
  // equal-power law lives in crossfade.js; MVP uses linear ramps.
  const switchRendition = async (target) => {
    if (!transportRef.current || active === target.id || fading) return;
    setError(null);
    try {
      ctxRef.current ??= resolveContext();
      const ctx = ctxRef.current;
      const from = renditions.find((r) => r.id === active);
      const fromBpm = from?.params?.tempo_bpm ?? doc.globals?.tempo?.bpm ?? 96;
      const toBpm = target.params?.tempo_bpm ?? doc.globals?.tempo?.bpm ?? 96;
      const position = transportRef.current.state().position;
      const { targetSeconds } = planSwitch(doc, position, fromBpm, toBpm);
      const targetBuffer = prerender(ctx, target);

      const FADE_S = 1.5;
      setFading(true);
      // Outgoing: pause at the end of the fade; incoming: start at the
      // mapped position and let the overlap play through.
      setTimeout(() => transportRef.current?.pause(), FADE_S * 1000);
      const incoming = createTransport(targetBuffer, ctx, { onstatechange: setState });
      transportRef.current = incoming;
      setActive(target.id);
      incoming.seek(targetSeconds);
      incoming.play();
      setTimeout(() => setFading(false), FADE_S * 1000);
    } catch (e) {
      setError(e.message);
      setFading(false);
    }
  };

  if (!renditions.length) return <p className="muted">no renditions to play</p>;
  const current = state ?? { playing: false, position: 0, duration: 0, ended: false };
  const activeRendition = renditions.find((r) => r.id === active);

  return (
    <div>
      <div className="cards">
        {renditions.map((r) => (
          <div className={`card ${active === r.id ? "card-active" : ""}`} key={r.id}>
            <h3>{r.name ?? r.id}</h3>
            <dl>
              {r.style?.genre && <><dt>genre</dt><dd>{r.style.genre}{r.style.era ? ` (${r.style.era})` : ""}</dd></>}
              {r.params?.tempo_bpm !== undefined && <><dt>tempo</dt><dd>{r.params.tempo_bpm} bpm</dd></>}
              {r.params?.instrumentation && <><dt>instruments</dt><dd>{r.params.instrumentation.map((i) => (typeof i === "string" ? i : i.name)).join(", ")}</dd></>}
            </dl>
            <button onClick={() => play(r)} disabled={loading}>
              {loading && active !== r.id ? "…" : active === r.id && current.playing ? "pause" : active === r.id ? "resume" : "play"}
            </button>
            {active && active !== r.id && (
              <button onClick={() => switchRendition(r)} disabled={fading} title="crossfade to this rendition at the current position">
                {fading ? "fading…" : "⇄ switch"}
              </button>
            )}
          </div>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {activeRendition && (
        <div className="transport">
          <span className="transport-title">{activeRendition.name ?? activeRendition.id}</span>
          <input
            type="range"
            min={0}
            max={current.duration}
            step={0.1}
            value={current.position}
            onChange={(e) => transportRef.current?.seek(Number(e.target.value))}
          />
          <span className="muted">{fmt(current.position)} / {fmt(current.duration)}</span>
          {sectionAt(doc, current.position, activeRendition?.params?.tempo_bpm) && (
            <span className="muted">§ {sectionAt(doc, current.position, activeRendition?.params?.tempo_bpm)}</span>
          )}
          <button onClick={stop}>stop</button>
        </div>
      )}
    </div>
  );
}
