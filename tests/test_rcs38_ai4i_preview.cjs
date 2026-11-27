"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const script = fs.readFileSync(path.join(__dirname, "../frontend/monitoring/ai4i_preview.js"), "utf8");
const html = fs.readFileSync(path.join(__dirname, "../frontend/monitoring/ai4i_preview.html"), "utf8");

function fixture(overrides = {}) {
  return {
    schema_version: "rcs38-ai4i-readonly-v0.1",
    source_mode: "industrial_proxy_non_medical",
    read_only: true,
    medical_data: false,
    clinical_use: false,
    control_enabled: false,
    x_axis: "source_record_id_not_time",
    actions: [],
    equipment: [{ id: "AI4I-L", type: "L" }],
    source: { id: "S04", nom: "<script>bad</script>", licence: "fixture",
      categorie: "Substitut synthétique non-medical", date_verif: "2026-11-23" },
    observations: [{
      equipment_id: "AI4I-L", source_record_id: "1",
      measurement: { air_temp_k: 300, process_temp_k: 310, rpm: 1400, torque_nm: 40 },
      anomaly: { score: null, threshold: null, flag: null },
      provenance: { source_id: "S04", file_sha256: "a".repeat(64) }
    }],
    ...overrides
  };
}
async function render(payload) {
  const elements = {};
  const get = id => (elements[id] ??= {
    hidden: true, textContent: "", innerHTML: "", files: [],
    children: [],
    replaceChildren() { this.children = []; },
    appendChild(node) { this.children.push(node); },
    addEventListener(name, fn) { this[name] = fn; }
  });
  const document = {
    getElementById: get,
    createElement: () => ({ innerHTML: "" }),
    createDocumentFragment: () => ({
      children: [],
      appendChild(node) { this.children.push(node); }
    })
  };
  vm.runInNewContext(script, { document }, { filename: "ai4i_preview.js" });
  get("proxy-file").files = [{ size: 2000, text: async () => JSON.stringify(payload) }];
  await get("proxy-file").change();
  return { elements, status: get("status").textContent };
}
test("accepts non-medical English spelling used by Python adapter", async () => {
  const out = await render(fixture());
  assert.match(out.status, /1 observations chargées/);
  assert.equal(out.elements.summary.hidden, false);
  assert.doesNotMatch(out.elements.source.innerHTML, /<script>/);
  assert.match(out.elements.source.innerHTML, /&lt;script&gt;/);
  const row = out.elements.observations.children[0].children[0];
  assert.match(row.innerHTML, /SHA-256 complet/);
  assert.match(row.innerHTML, new RegExp("a".repeat(64)));
  assert.match(row.innerHTML, /ND/);
});
test("shows read-only mode in visible banner", () => {
  assert.match(html, /<div class="demo-label">SUBSTITUT INDUSTRIEL · NON MÉDICAL · LECTURE SEULE<\/div>/);
});

test("defines ND as not available/not scored, not normal", () => {
  assert.match(html, /ND = non disponible ou non scoré/);
  assert.match(html, /ND ne signifie pas « normal »/);
});
test("rejects equipment not present in declared inventory", async () => {
  const data = fixture();
  data.observations[0].equipment_id = "AI4I-UNKNOWN";
  const out = await render(data);
  assert.match(out.status, /Export non chargé/);
  assert.equal(out.elements.summary.hidden, true);
});
test("rejects medical source, clinical flag and any actions", async () => {
  for (const patch of [
    { source: { ...fixture().source, categorie: "medical device data" } },
    { medical_data: true },
    { actions: [{ id: "fake" }] },
    { control_enabled: true }
  ]) {
    const out = await render(fixture(patch));
    assert.match(out.status, /Export non chargé/);
    assert.equal(out.elements.results.hidden, true);
  }
});
test("rejects missing SHA-256 provenance", async () => {
  const data = fixture();
  data.observations[0].provenance.file_sha256 = "wrong";
  const out = await render(data);
  assert.match(out.status, /Export non chargé/);
});
test("does not call fetch or network APIs", () => {
  assert.doesNotMatch(script, /\bfetch\s*\(/);
  assert.doesNotMatch(script, /\bXMLHttpRequest\b/);
  assert.doesNotMatch(script, /\bWebSocket\b/);
});
