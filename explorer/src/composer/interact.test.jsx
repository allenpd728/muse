// Component-level DOM interaction (issue #118): the composer shell mounted
// in jsdom — a real React render, real event dispatch. Pins the interactive
// surface the data-layer tests can't reach.
import { describe, it, expect, beforeAll } from "vitest";
import { readFile } from "node:fs/promises";

let React, act, createRoot, full;

const flush = () => new Promise((r) => setTimeout(r, 50));

beforeAll(async () => {
  const { JSDOM } = await import("jsdom");
  const dom = new JSDOM("<!doctype html><html><body><div id=\"root\"></div></body></html>", { url: "http://localhost/" });
  globalThis.document = dom.window.document;
  globalThis.window = dom.window;
  Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });
  globalThis.ResizeObserver ??= class { observe() {} unobserve() {} disconnect() {} };
  for (const name of ["SVGElement", "SVGGraphicsElement", "DOMMatrixReadOnly"])
    globalThis[name] ??= dom.window[name] ?? class {};
  globalThis.fetch = async () => ({ ok: true, text: async () => JSON.stringify(full) });
  React = (await import("react")).default;
  act = (await import("react")).act;
  createRoot = (await import("react-dom/client")).createRoot;
  full = JSON.parse(await readFile(new URL("../../../examples/full.muse.json", import.meta.url), "utf8"));
});

describe("composer shell DOM interaction (issue #118)", () => {
  it("loads an example, selects a node, edits a scalar field through the inspector", async () => {
    const { default: Composer } = await import("./main.jsx").catch(() => ({}));
    // main.jsx mounts itself on import when #root exists; import triggers the render.
    await import("./main.jsx");
    await act(flush);

    // Click the "full example" button to load a document.
    const loadBtn = [...document.querySelectorAll("button")].find((b) => b.textContent.includes("full example"));
    expect(loadBtn).toBeTruthy();
    await act(async () => { loadBtn.dispatchEvent(new window.MouseEvent("click", { bubbles: true })); });
    await act(flush);

    // A section node should be present in the canvas.
    const sectionNode = [...document.querySelectorAll(".react-flow__node")].find((n) => n.textContent.includes("verse.1"));
    expect(sectionNode).toBeTruthy();
    await act(async () => { sectionNode.dispatchEvent(new window.MouseEvent("click", { bubbles: true })); });
    await act(flush);

    // Inspector shows the section's scalar fields.
    const barsInput = [...document.querySelectorAll(".field input")].find((i) => i.previousSibling?.textContent === "bars");
    expect(barsInput).toBeTruthy();
    expect(barsInput.value).toBe("16");

    // Edit bars through the inspector: the edit flows through applyGraph → compile.
    await act(async () => {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(barsInput, "24");
      barsInput.dispatchEvent(new window.Event("input", { bubbles: true }));
    });
    await act(flush);
    expect(barsInput.value).toBe("24");
  });
});
