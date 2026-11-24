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
let serviceOnline = false, requestBusy = false;
const byId = (id) => document.getElementById(id);
const escapeHtml = (val) => String(val ?? "").replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const formatND = (val, unit="") => val === null || val === undefined || val === "" ? "ND" :
  String(val) + (unit ? " " + unit : "");
function badge(status) {
  const key = String(status || "ND");
  const cls = ["alerte","à vérifier","invalide","ouvert","en attente"].includes(key.toLowerCase()) ? "warn" :
    ["critique","rejetée"].includes(key.toLowerCase()) ? "critical" :
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
  const rows=readings.map(d=>`<tr><td>${escapeHtml(d.device)}</td><td>${escapeHtml(d.site)}</td><td>${escapeHtml(formatND(d.value,d.unit))}</td><td>${badge(d.quality)}</td><td>${badge(d.anomaly?"Alerte":"Non signalée")}</td></tr>`);
  return `<div class="metric-grid">${cards}</div><div class="panels">${panel("Observations fictives",table(["Équipement","Site","Mesure (démo)","Qualité","Signal"],rows))}${panel("Contrôles nécessaires",`<div class="summary">${row("Vérité terrain","ND")}${row("Précision / rappel","ND")}${row("Dérive des données","À définir")}${row("Métriques par sous-groupe","À définir")}</div><p class="hint">Une donnée invalide ne doit jamais servir de preuve de panne. RCS-69 et RCS-88 encadrent les évaluations scientifiques.</p>`)}</div>`;
}
function maintenance(){
  const actions=selected(data.actions);
  const pending=actions.filter(x=>x.state==="En attente").length;
  const controls=(a)=>{
    if(!serviceOnline || a.state!=="En attente")return serviceOnline?"—":'<span class="tag nd">API locale non activée</span>';
    const id=escapeHtml(a.id);
    return '<div class="decision-controls">'+
      '<label class="confirmation-label"><input type="checkbox" class="simulation-confirm" id="confirm-'+id+'"> Confirmation : simulation uniquement</label>'+
      '<button type="button" class="action-btn approve" data-action-id="'+id+'" data-decision="approved">Approuver (démo)</button>'+
      '<label class="reason-label" for="reason-'+id+'">Motif du rejet'+
      '<select id="reason-'+id+'" class="reason-select">'+
      '<option value="signal_non_confirme">Signal non confirmé</option>'+
      '<option value="qualite_insuffisante">Qualité insuffisante</option>'+
      '</select></label>'+
      '<button type="button" class="action-btn reject" data-action-id="'+id+'" data-decision="rejected">Rejeter (démo)</button>'+
      '</div>';
  };
  const rows=actions.map(x=>'<tr><td>'+escapeHtml(x.id)+'</td><td>'+escapeHtml(x.device)+'</td><td>'+escapeHtml(x.site)+'</td><td>'+escapeHtml(x.reason)+'</td><td>'+badge(x.state)+'</td><td>'+controls(x)+'</td></tr>');
  const filteredEvents=(data.events||[]).filter(x=>chosenSite==="all" || actions.some(a=>a.id===x.action_id && a.site===chosenSite));
  const eventRows=filteredEvents.map(x=>'<tr><td><code>'+escapeHtml(x.trace_id.slice(0,8))+'</code></td><td>'+escapeHtml(x.action_id)+'</td><td>'+badge(x.after_state)+'</td><td>'+escapeHtml(x.reason_code)+'</td><td>'+escapeHtml(x.actor_role || 'ND')+'</td><td>'+escapeHtml(x.created_at)+'</td></tr>');
  const cards=metric("Actions fictives",actions.length,"État SQLite en mode API")+
    metric("En attente",pending,"Confirmation explicite")+
    metric("Décisions simulées",filteredEvents.length,"Journal de traces non clinique")+
    metric("Interventions réelles","ND","Aucune machine connectée");
  return '<div class="metric-grid">'+cards+'</div><div class="panels">'+
    panel("Alertes et validation humaine simulée",table(["Référence","Équipement","Site","Motif","État","Décision fictive"],rows),true)+
    panel("Historique des décisions — identifiant de trace",table(["Trace","Action","Décision","Motif","Rôle simulé","Date UTC"],eventRows),true)+
    panel("Workflow et limites",'<div class="summary">'+
      row("1. Alerte","Création / journal")+row("2. Contrôle","Qualité et contexte")+
      row("3. Décision","Simulation de technicien")+row("4. Traçabilité","SQLite locale + trace_id")+
      row("Authentification réelle","Non implémentée")+'</div>'+
      '<p class="hint">Aucune commande biomédicale. Les décisions simulées ne déclenchent aucune intervention. Ne pas déployer sur Internet.</p>',true)+'</div>';
}
function platform(){
  const runs=selected(data.runs);
  const knownCosts=runs.filter(r=>r.cost_eur!==null);
  const costSum=knownCosts.reduce((sum,r)=>sum+r.cost_eur,0);
  const p95="ND"; // Ne pas calculer une latence p95 sur une liste de démonstration non gelée.
  const rows=runs.map(x=>`<tr><td>${escapeHtml(x.run_id)}</td><td>${escapeHtml(x.model)}</td><td>${escapeHtml(x.version)}</td><td>${escapeHtml(formatND(x.latency_ms,"ms"))}</td><td>${escapeHtml(formatND(x.cost_eur,"€"))}</td><td>${escapeHtml(formatND(x.energy_kwh,"kWh"))}</td><td>${badge(x.boundary)}</td></tr>`);
  const cards=[metric("Exécutions fictives",runs.length,"Illustration sans appel LLM"),metric("Coût d'exemple",knownCosts.length===runs.length&&runs.length ? costSum.toFixed(3)+" €":"ND","Montant fictif, pas une facture"),metric("Latence p95",p95,"Pas de benchmark gelé"),metric("Énergie distante","ND","Non observable via CodeCarbon local")].join("");
  return `<div class="metric-grid">${cards}</div><div class="panels">${panel("Exécutions pédagogiques",table(["Run fictif","Modèle","Version","Latence","Coût","Énergie","Frontière"],rows),true)}${panel("Couverture Green AI / gouvernance",`<div class="summary">${row("CPU/GPU local CodeCarbon","Non instrumenté")}${row("Énergie LLM distant","ND")}${row("Provenance des données","Fictive")}${row("Modèles A/B réels","Non choisis")}${row("Coût par tâche réussie","ND")}${row("Biais et drift","Non évalués")}</div><p class="hint">Les coûts de démonstration ne sont pas des montants payés. CodeCarbon n'observe pas les serveurs des API distantes. RCS-81/82/83/87/89/90 définissent le futur suivi mesuré.</p>`,true)}</div>`;
}
function render(){
  if(!data) return;
  const selectedTitle=views.find(v=>v.id===chosenView).title;
  byId("section-title").textContent=selectedTitle;
  // Preserve the focused navigation button when switching views with a keyboard.
  if(!byId("nav").children.length)
    byId("nav").innerHTML=views.map((v,i)=>`<button class="nav-btn" type="button" data-view="${v.id}"><span class="nav-num">${i+1}</span> ${escapeHtml(v.short)}</button>`).join("");
  for(const button of byId("nav").querySelectorAll("button[data-view]"))
    button.setAttribute("aria-current",button.dataset.view===chosenView?"page":"false");
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
function announce(message,isError=false){
  const field=byId("feedback");
  field.hidden=false;
  field.className="feedback"+(isError?" error":"");
  field.textContent=message;
}
function initializeSites(){
  const select=byId("site-filter");
  const previous=select.value;
  while(select.options.length>1)select.remove(1);
  const sites=[...new Set(data.devices.map(d=>d.site))].sort((a,b)=>a.localeCompare(b));
  for(const site of sites){
    const option=document.createElement("option");
    option.value=site;
    option.textContent=site+" (fictif)";
    select.append(option);
  }
  select.value=sites.includes(previous)?previous:"all";
  chosenSite=select.value;
}
async function refreshDemo(){
  const response=await fetch("/api/v1/demo/overview",{cache:"no-store"});
  if(!response.ok)throw Error("API locale inaccessible");
  const json=await response.json();
  if(json.data_mode!=="fictional_demo_only" || json.server_mode!=="local_demo")
    throw Error("Source de démonstration non vérifiée");
  data=json;
  serviceOnline=true;
  initializeSites();
  render();
}
byId("content").addEventListener("click",async event=>{
  const button=event.target.closest("button[data-action-id]");
  if(!button || requestBusy)return;
  if(!serviceOnline)return announce("L'API locale doit être démarrée pour valider une simulation.",true);
  const action=button.dataset.actionId;
  const decision=button.dataset.decision;
  const check=byId("confirm-"+action);
  if(!check || !check.checked){
    announce("Cochez la confirmation : simulation uniquement.",true);
    return;
  }
  const reasonCode=decision==="approved"?"controle_confirme":byId("reason-"+action).value;
  requestBusy=true;
  button.disabled=true;
  try{
    const response=await fetch("/api/v1/demo/actions/"+encodeURIComponent(action)+"/decision",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        decision:decision,reason_code:reasonCode,acknowledge_simulation:true
      })
    });
    const result=await response.json();
    if(!response.ok)throw Error(result.error||"Réponse API invalide");
    await refreshDemo();
    announce("Décision fictive enregistrée (trace "+result.trace_id.slice(0,8)+"). Aucune machine réelle concernée.");
  }catch(error){
    announce("Échec de la validation simulée : "+error.message,true);
    try{await refreshDemo();}catch(_){/* conservation du dernier affichage sûr */}
  }finally{
    requestBusy=false;
    button.disabled=false;
  }
});
(async()=>{
  try{
    await refreshDemo();
    announce("API locale connectée : décisions fictives tracées dans SQLite. Aucun accès à une machine réelle.");
  }catch(_){
    try{
      const response=await fetch("./demo.json",{cache:"no-store"});
      if(!response.ok)throw Error("Fixtures non accessibles");
      const json=await response.json();
      if(json.data_mode!=="fictional_demo_only")throw Error("Source non fictive refusée");
      data=json;
      serviceOnline=false;
      initializeSites();
      render();
      announce("Lecture seule : pour tester les validations simulées, lancer python -m tools.rcs38_demo_server.");
    }catch(error){
      byId("content").textContent="Chargement impossible : vérifier le serveur et les données.";
      announce("Erreur : "+error.message,true);
    }
  }
})();
