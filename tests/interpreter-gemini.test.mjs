// Gemini adapter shape pins (issue #106): wire shape, structured-JSON request,
// env resolution — no live calls in npm test (live smoke stays manual).
// Standalone runner; folded into npm test.
import { defaultModelConfig } from "../interpreter/expand.mjs";

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

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
