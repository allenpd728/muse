// Gemini adapter shape pins (issue #106): wire shape, structured-JSON request,
// env resolution — no live calls in npm test (live smoke stays manual).
// Residual coverage appended per tests/open_20260822-204500_gemini-adapter.md
// (issue #110).
// Standalone runner; folded into npm test.
import { defaultModelConfig, expand } from "../interpreter/expand.mjs";

let passed = 0, failed = 0;
const check = (name, cond) => {
  if (cond) { passed++; console.log(`ok   ${name}`); }
  else {
    failed++;
    console.error(`FAIL ${name}`);
  }
};

// defaultModelConfig resolves the gemini provider without touching the offline path.
const cfg = defaultModelConfig({ MUSE_PROVIDER: "gemini", MUSE_MODEL: "gemini-2.0-flash", GEMINI_API_KEY: "test-key" });
check("gemini provider resolves", typeof cfg.callModel === "function" && cfg.model === "gemini-2.0-flash");
check("missing GEMINI_API_KEY errors", (() => { try { defaultModelConfig({ MUSE_PROVIDER: "gemini", MUSE_MODEL: "x" }); return false; } catch { return true; } })());

// Wire shape: intercept fetch, assert the request, return a canned response.
const calls = [];
globalThis.fetch = async (url, init) => {
  calls.push({ url, init });
  return {
    ok: true,
    json: async () => ({ candidates: [{ content: { parts: [{ text: "{\"muse_perf_version\":\"0.1.0\"}" }] } }] }),
  };
};

const prompt = { system: "sys", user: "usr" };
const out = await cfg.callModel(prompt);

check("endpoint is the Gemini generateContent path", calls[0].url === "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=test-key");
const body = JSON.parse(calls[0].init.body);
check("structured JSON requested (responseMimeType)", body.generationConfig?.responseMimeType === "application/json");
check("system + user messages mapped to Gemini roles", body.system_instruction?.parts?.[0]?.text === "sys" && body.contents?.[0]?.role === "user" && body.contents?.[0]?.parts?.[0]?.text === "usr");
check("adapter surfaces the text for the parse/retry loop", out === "{\"muse_perf_version\":\"0.1.0\"}");

// --- Residual coverage (issue #110) ---

// Error surface: non-OK responses throw with status + body text, readable
// enough for the retry loop to feed back.
{
  globalThis.fetch = async () => ({ ok: false, status: 429, text: async () => "rate limit exceeded: quota 50/day" });
  let err = null;
  try { await cfg.callModel(prompt); } catch (e) { err = e; }
  check("429 surfaces status + body in the thrown error",
    err !== null && err.message.includes("429") && err.message.includes("rate limit"));
  globalThis.fetch = async () => ({ ok: false, status: 400, text: async () => "API key not valid" });
  err = null;
  try { await cfg.callModel(prompt); } catch (e) { err = e; }
  check("400 bad key surfaces status + body", err !== null && err.message.includes("400") && err.message.includes("API key not valid"));
}

// Retry loop integration: a prose-wrapped JSON response fails parsing,
// feeds feedback to the model, and a clean second response succeeds.
{
  const minimal = JSON.parse(await (await import("node:fs/promises")).readFile(new URL("../examples/minimal.muse.json", import.meta.url), "utf8"));
  const fixture = JSON.parse(await (await import("node:fs/promises")).readFile(new URL("../interpreter/fixtures/minimal-expansion.muse.perf.json", import.meta.url), "utf8"));
  const calls2 = [];
  globalThis.fetch = async (url, init) => {
    calls2.push({ url, init });
    const attempt = calls2.length;
    const text = attempt === 1
      ? "Here is the performance document you asked for:\n\n```json\n" + JSON.stringify(fixture) + "\n```"
      : JSON.stringify(fixture);
    return { ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text }] } }] }) };
  };
  const { perf, attempts } = await expand({
    doc: minimal,
    callModel: cfg.callModel,
    model: "gemini-2.0-flash",
    at: "2026-08-22T21:00:00Z",
  });
  check("prose-wrapped JSON retries with feedback, clean second response succeeds",
    attempts === 2 && !!perf);
  check("retry feedback mentions the parse failure",
    JSON.parse(calls2[1].init.body).contents[0].parts[0].text.includes("previous attempt failed validation"));
}

// MUSE_BASE_URL override applies to the gemini adapter.
{
  const proxied = defaultModelConfig({ MUSE_PROVIDER: "gemini", MUSE_MODEL: "gemini-2.0-flash", GEMINI_API_KEY: "k", MUSE_BASE_URL: "http://localhost:9999" });
  const seen = [];
  globalThis.fetch = async (url, init) => {
    seen.push(url);
    return { ok: true, json: async () => ({ candidates: [{ content: { parts: [{ text: "{}" }] } }] }) };
  };
  await proxied.callModel(prompt);
  check("MUSE_BASE_URL override applies to gemini", seen[0].startsWith("http://localhost:9999/"));
}

// Model default (reconciled): gemini falls back to the free-tier flash model
// per the README; other providers still require explicit MUSE_MODEL.
check("gemini without MUSE_MODEL defaults to the current free-tier flash",
  defaultModelConfig({ MUSE_PROVIDER: "gemini", GEMINI_API_KEY: "k" }).model === "gemini-3.6-flash");
check("MUSE_MODEL wins over the gemini default",
  defaultModelConfig({ MUSE_PROVIDER: "gemini", MUSE_MODEL: "gemini-2.5-pro", GEMINI_API_KEY: "k" }).model === "gemini-2.5-pro");
check("anthropic without MUSE_MODEL still errors (no hard-coded default)",
  (() => { try { defaultModelConfig({ MUSE_PROVIDER: "anthropic", ANTHROPIC_API_KEY: "k" }); return false; } catch { return true; } })());

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
