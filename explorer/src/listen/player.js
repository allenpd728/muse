// WebAudio playback core (docs/scope-listener.md, task 1): performance
// document → playable transport over player/render.mjs. The render math is
// reused, never ported — this module owns only AudioContext plumbing.
// Pure (no DOM at import time): AudioContext is injected or resolved lazily,
// so node can exercise the buffer logic with a stub.
import { render } from "../../../player/render-core.mjs";

const resolveContext = (injected) => {
  if (injected) return injected;
  const AC = globalThis.AudioContext ?? globalThis.webkitAudioContext;
  if (!AC) throw new Error("WebAudio unavailable in this environment");
  return new AC();
};

// Float32Array[] channels → an AudioBuffer-shaped object. Works with a real
// AudioContext or a stub exposing { sampleRate, createBuffer }.
export function buildBuffer(ctx, channels, sampleRate) {
  const frames = channels[0]?.length ?? 0;
  const buffer = ctx.createBuffer(channels.length, frames, sampleRate);
  channels.forEach((data, i) => {
    if (buffer.copyToChannel) buffer.copyToChannel(data, i);
    else buffer.getChannelData(i).set(data);
  });
  return buffer;
}

// Render a performance document straight to a buffer (convenience for the
// Listen tab; the heavy lifting stays in player/render.mjs).
export function renderToBuffer(ctx, perfDoc, { sampleRate = 44100 } = {}) {
  return buildBuffer(ctx, render(perfDoc, { sampleRate }), sampleRate);
}

// A minimal transport: play/pause/seek/stop over one rendered buffer,
// tracking position across pauses. Events: onstatechange(state) with
// { playing, position, duration, ended }.
export function createTransport(buffer, ctx, { onstatechange } = {}) {
  let source = null;
  let startedAt = 0;     // ctx.currentTime when the current source started
  let offset = 0;        // accumulated position (seconds) excluding current run
  let playing = false;
  let ended = false;

  const position = () =>
    playing ? Math.min(buffer.duration, offset + (ctx.currentTime - startedAt)) : offset;

  const emit = () =>
    onstatechange?.({ playing, position: position(), duration: buffer.duration, ended });

  const startSource = (at) => {
    source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);
    source.onended = () => {
      if (playing && position() >= buffer.duration - 1e-3) {
        playing = false;
        ended = true;
        offset = 0;
        emit();
      }
    };
    source.start(0, at);
  };

  return {
    play() {
      if (playing) return;
      if (ended) { ended = false; offset = 0; }
      if (ctx.state === "suspended") ctx.resume();
      startedAt = ctx.currentTime;
      playing = true;
      startSource(offset);
      emit();
    },
    pause() {
      if (!playing) return;
      offset = position();
      playing = false;
      source.onended = null;
      source.stop();
      emit();
    },
    seek(seconds) {
      const clamped = Math.max(0, Math.min(buffer.duration, seconds));
      const wasPlaying = playing;
      if (playing) { source.onended = null; source.stop(); }
      offset = clamped;
      ended = false;
      if (wasPlaying) { startedAt = ctx.currentTime; startSource(offset); }
      emit();
    },
    stop() {
      if (source) { source.onended = null; try { source.stop(); } catch {} }
      playing = false;
      ended = false;
      offset = 0;
      emit();
    },
    state: () => ({ playing, position: position(), duration: buffer.duration, ended }),
  };
}

export { resolveContext };
