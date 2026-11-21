"use strict";
// RCS-38 — interface entièrement déconnectée, données fictives et validées.
// Pas de connexion hospitalière, d'appel externe, de décision automatisée.
const views = [
  {id:"equipment",title:"Parc des équipements",short:"Équipements"},
  {id:"data",title:"Qualité des données & anomalies",short:"Données & anomalies"},
  {id:"maintenance",title:"Maintenance & interventions",short:"Maintenance"},
  {id:"platform",title:"Plateforme & Green AI",short:"Plateforme / Green AI"}
];
let data = null, chosenView = "equipment", chosenSite = "all";
const byId = (id) => document.getElementById(id);
const escapeHtml = (val) => String(val ?? "").replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const formatND = (val, unit="") => val === null || val === undefined || val === "" ? "ND" :
  String(val) + (unit ? " " + unit : "");
function badge(status) {
  const key = String(status || "ND");
  const cls = ["alerte","à vérifier","invalide","ouvert","en attente"].includes(key.toLowerCase()) ? "warn" :
    key.toLowerCase() === "critique" ? "critical" :
    key === "ND" ? "nd" : "";
  return `<span class="tag ${cls}">${escapeHtml(key)}</span>`;
}
function metric(label,value,desc="") {
  return `<article class="metric"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><div class="sub">${escapeHtml(desc)}</div></article>`;
}
function row(label,value) {
  return `<div class="summary-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}
function panel(title,html,full=false) {
  return `<section class="panel ${full?"full":""}"><h2>${escapeHtml(title)}</h2>${html}</section>`;
}
function table(headers,rows) {
  return `<table><thead><tr>${headers.map(s=>`<th scope="col">${escapeHtml(s)}</th>`).join("")}</tr></thead><tbody>${rows.join("") || `<tr><td colspan="${headers.length}">Aucune donnée fictive pour ce filtre.</td></tr>`}</tbody></table>`;
}
function selected(collection) {
  return collection.filter(x => chosenSite === "all" || x.site === chosenSite || x.site === "all");
}
function equipment() {
  const devices = selected(data.devices);
  const checking = devices.filter(d=>d.status==="À vérifier").length;
  const cards = [metric("Appareils fictifs",devices.length,"Inventaire de démonstration"),metric("En vérification",checking,"Aucune action automatique"),metric("Familles simulées",new Set(devices.map(x=>x.family)).size,"Famille pilote non décidée"),metric("Disponibilité réelle","ND","Aucun équipement connecté")].join("");
  const rows = devices.map(d=>`<tr><td>${escapeHtml(d.id)}</td><td>${escapeHtml(d.family)}</td><td>${escapeHtml(d.site)}</td><td>${badge(d.status)}</td></tr>`);
  return `<div class="metric-grid">${cards}</div><div class="panels">${panel("Parc fictif",table(["ID démo","Type","Site","État déclaré"],rows))}${panel("Règles métier",`<div class="summary">${row("Connexion machine","Aucune")}${row("Décisions automatiques","Interdites")}${row("Validation des alertes","Technicien habilité")}${row("Famille pilote","À confirmer")}</div><p class="hint">Exemple pédagogique : les noms et identifiants ne représentent aucun matériel réel.</p>`)}</div>`;
}
function dataQuality(){
  const readings=selected(data.readings);
  const anomalies=readings.filter(x=>x.anomaly===true);
  const invalid=readings.filter(x=>x.quality!=="valide");
  const cards=[metric("Échantillons fictifs",readings.length,"Données simulées"),metric("Alertes candidates",anomalies.length,"À vérifier par un humain"),metric("Données invalides",invalid.length,"Aucune interprétation clinique"),metric("Taux de faux négatifs","ND","Absence de vérité terrain")].join("");
  const rows=readings.map(d=>`<tr><td>${escapeHtml(d.device)}</td><td>${escapeHtml(d.site)}</td><td>${formatND(d.value,d.unit)}</td><td>${badge(d.quality)}</td><td>${badge(d.anomaly?"Alerte":"Non signalée")}</td></tr>`);
  return `<div class="metric-grid">${cards}</div><div class="panels">${panel("Observations fictives",table(["Équipement","Site","Mesure (démo)","Qualité","Signal"],rows))}${panel("Contrôles nécessaires",`<div class="summary">${row("Vérité terrain","ND")}${row("Précision / rappel","ND")}${row("Dérive des données","À définir")}${row("Métriques par sous-groupe","À définir")}</div><p class="hint">Une donnée invalide ne doit jamais servir de preuve de panne. RCS-69 et RCS-88 encadrent les évaluations scientifiques.</p>`)}</div>`;
}
function maintenance(){
  const actions=selected(data.actions);
  const pending=actions.filter(x=>x.state==="En attente").length;
  const rows=actions.map(x=>`<tr><td>${escapeHtml(x.id)}</td><td>${escapeHtml(x.device)}</td><td>${escapeHtml(x.site)}</td><td>${escapeHtml(x.reason)}</td><td>${badge(x.state)}</td></tr>`);
  return `<div class="metric-grid">${metric("Actions fictives",actions.length,"Historique pédagogique")}${metric("À valider",pending,"Technicien requis")}${metric("Interventions réelles","ND","Aucune machine connectée")}${metric("Temps moyen de résolution","ND","Pas de mesures réelles")}</div><div class="panels">${panel("Interventions simulées",table(["Référence","Équipement","Site","Motif","Statut"],rows),true)}${panel("Workflow cible",`<div class="summary">${row("1. Alerte","Création / journal")}${row("2. Contrôle","Qualité et contexte")}${row("3. Décision","Technicien habilité")}${row("4. Traçabilité","Intervention et approbation")}</div><p class="hint">Le prototype n'autorise aucune intervention sur une machine réelle.</p>`,true)}</div>`;
}
function platform(){
  const runs=selected(data.runs);
  const knownCosts=runs.filter(r=>r.cost_eur!==null);
  const costSum=knownCosts.reduce((sum,r)=>sum+r.cost_eur,0);
  const p95="ND"; // Ne pas calculer une latence p95 sur une liste de démonstration non gelée.
  const rows=runs.map(x=>`<tr><td>${escapeHtml(x.run_id)}</td><td>${escapeHtml(x.model)}</td><td>${escapeHtml(x.version)}</td><td>${formatND(x.latency_ms,"ms")}</td><td>${formatND(x.cost_eur,"€")}</td><td>${formatND(x.energy_kwh,"kWh")}</td><td>${badge(x.boundary)}</td></tr>`);
  const cards=[metric("Exécutions fictives",runs.length,"Illustration sans appel LLM"),metric("Coût d'exemple",knownCosts.length===runs.length&&runs.length ? costSum.toFixed(3)+" €":"ND","Montant fictif, pas une facture"),metric("Latence p95",p95,"Pas de benchmark gelé"),metric("Énergie distante","ND","Non observable via CodeCarbon local")].join("");
  return `<div class="metric-grid">${cards}</div><div class="panels">${panel("Exécutions pédagogiques",table(["Run fictif","Modèle","Version","Latence","Coût","Énergie","Frontière"],rows),true)}${panel("Couverture Green AI / gouvernance",`<div class="summary">${row("CPU/GPU local CodeCarbon","Non instrumenté")}${row("Énergie LLM distant","ND")}${row("Provenance des données","Fictive")}${row("Modèles A/B réels","Non choisis")}${row("Coût par tâche réussie","ND")}${row("Biais et drift","Non évalués")}</div><p class="hint">Les coûts de démonstration ne sont pas des montants payés. CodeCarbon n'observe pas les serveurs des API distantes. RCS-81/82/83/87/89/90 définissent le futur suivi mesuré.</p>`,true)}</div>`;
}
function render(){
  if(!data) return;
  const selectedTitle=views.find(v=>v.id===chosenView).title;
  byId("section-title").textContent=selectedTitle;
  byId("nav").innerHTML=views.map((v,i)=>`<button class="nav-btn" type="button" data-view="${v.id}" aria-current="${chosenView===v.id?"page":"false"}"><span class="nav-num">${i+1}</span> ${escapeHtml(v.short)}</button>`).join("");
  const renderers={equipment,data:dataQuality,maintenance,platform};
  byId("content").innerHTML=renderers[chosenView]();
}
byId("nav").addEventListener("click",e=>{
  const button=e.target.closest("button[data-view]");
  if(!button)return;
  chosenView=button.dataset.view;
  render();
});
byId("site-filter").addEventListener("change",e=>{chosenSite=e.target.value;render();});
fetch("./demo.json",{cache:"no-store"})
  .then(resp=>{if(!resp.ok)throw new Error("Données de démo introuvables");return resp.json();})
  .then(json=>{
    if(json.data_mode!=="fictional_demo_only")throw new Error("La source n'est pas déclarée fictive : affichage bloqué");
    data=json;
    const sites=[...new Set(json.devices.map(d=>d.site))].sort((a,b)=>a.localeCompare(b));
    for(const site of sites){const option=document.createElement("option");option.value=site;option.textContent=site+" (fictif)";byId("site-filter").append(option);}
    render();
  })
  .catch(err=>{byId("content").innerHTML=`<div class="empty">Échec du chargement. Ouvrir via un serveur HTTP local (python -m http.server). Aucune donnée réelle n'a été chargée.</div>`;console.error(err.message)});
