"use strict";
(function () {
  const fileInput = document.getElementById("proxy-file");
  const status = document.getElementById("status");
  const summary = document.getElementById("summary");
  const results = document.getElementById("results");
  const source = document.getElementById("source");
  const observations = document.getElementById("observations");
  const text = (value) => value === null || value === undefined ? "ND" : String(value);
  const escape = (value) => text(value).replace(/[&<>"']/g, c =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const td = (value) => "<td>" + escape(value) + "</td>";
  function check(json) {
    if (!json || typeof json !== "object" ||
        json.schema_version !== "rcs38-ai4i-readonly-v0.1" ||
        json.source_mode !== "industrial_proxy_non_medical" ||
        json.read_only !== true || json.medical_data !== false ||
        json.clinical_use !== false || json.control_enabled !== false ||
        json.x_axis !== "source_record_id_not_time" ||
        !Array.isArray(json.equipment) ||
        !Array.isArray(json.observations) ||
        !Array.isArray(json.actions) || json.actions.length !== 0 ||
        !json.source || json.source.id !== "S04" ||
        !/non[ -]médical/i.test(json.source.categorie || "")) {
      throw new Error("Contrat invalide : seul l'export AI4I non médical, strictement en lecture seule, est accepté.");
    }
    if (json.observations.length > 1000) {
      throw new Error("Trop d'observations. Produire un export limité à 1000 lignes.");
    }
    for (const obs of json.observations) {
      if (!obs || typeof obs !== "object" ||
          typeof obs.equipment_id !== "string" ||
          !obs.equipment_id.startsWith("AI4I-") ||
          !obs.provenance || obs.provenance.source_id !== "S04" ||
          !/^[a-fA-F0-9]{64}$/.test(obs.provenance.file_sha256 || "") ||
          !obs.measurement || !obs.anomaly) {
        throw new Error("Observation sans provenance fiable ou avec équipement non autorisé.");
      }
    }
    return json;
  }
  async function load() {
    summary.hidden = true;
    results.hidden = true;
    observations.replaceChildren();
    source.replaceChildren();
    const file = fileInput.files && fileInput.files[0];
    if (!file) { status.textContent = "Aucun fichier sélectionné."; return; }
    if (file.size > 2 * 1024 * 1024) {
      status.textContent = "Fichier refusé : taille supérieure à 2 Mo."; return;
    }
    try {
      const data = check(JSON.parse(await file.text()));
      source.innerHTML = "<p><strong>" + escape(data.source.nom) +
        "</strong> · Licence : " + escape(data.source.licence) +
        " · Catégorie : " + escape(data.source.categorie) +
        " · Vérification : " + escape(data.source.date_verif) + "</p>" +
        "<p>Type : substitut industriel synthétique non médical. " +
        "Aucune connexion avec un équipement ou un patient.</p>";
      const fragment = document.createDocumentFragment();
      for (const obs of data.observations) {
        const m = obs.measurement, a = obs.anomaly;
        const tr = document.createElement("tr");
        const score = a.score === null || a.threshold === null ?
          "ND" : text(a.score) + " / " + text(a.threshold) +
          (a.flag === true ? " · alerte candidate" : "");
        tr.innerHTML = td(obs.equipment_id) + td(obs.source_record_id) +
          td(m.air_temp_k) + td(m.process_temp_k) + td(m.rpm) +
          td(m.torque_nm) + td(score) +
          td(obs.provenance.file_sha256.slice(0, 12) + "…");
        fragment.appendChild(tr);
      }
      observations.appendChild(fragment);
      status.textContent = data.observations.length +
        " observations chargées localement. Lecture seule, sans décision possible.";
      summary.hidden = false;
      results.hidden = false;
    } catch (error) {
      status.textContent = "Export non chargé : " + error.message;
    }
  }
  fileInput.addEventListener("change", load);
})();
