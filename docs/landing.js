"use strict";
// Site institutionnel de démonstration, sans cookies, traceur ni API distante.
// Les onglets de recherche donnent des EXPLICATIONS, pas des résultats mesurés.
const tracks={
  j1:{
    num:"J1",tag:"GENAI · CM03 · 60 MIN",
    title:"Diffusion-based anomaly detection",
    description:"Comparer un véritable modèle génératif de diffusion à une baseline sur 8–10 cas gelés, documenter les paramètres, la reproductibilité et au moins un échec. Les données industrielles/simulées restent non médicales.",
    meta:["État : préparation", "Aucun modèle médical validé"]},
  j2:{
    num:"J2",tag:"MULTI-LLM · TP04 · 120 + 30 MIN",
    title:"Two LLMs, one evidence-based workflow",
    description:"Identifier deux LLM réels A/B, comparer mono-A, mono-B et V2 (routing/cascade) sur les mêmes dix cas, dont quatre stress. Contrôler fidélité aux sources, refus, latence et coûts.",
    meta:["État : protocole préparé", "Benchmark réel non exécuté"]},
  tp05:{
    num:"05",tag:"FINOPS · GREEN AI · ÉTHIQUE · 90 MIN",
    title:"Sustainable, observable and responsible AI",
    description:"Sur le workload du TP04, mesurer ou qualifier le coût par réussite, l'empreinte locale et les limites des API distantes ; enregistrer au moins trois risques éthiques et un test traçable. TP05 complète J2.",
    meta:["État : outillage préparé", "Mesures réelles : ND"]}
};
const buttons=Array.from(document.querySelectorAll("[data-track]"));
const panel=document.getElementById("track-content");
function displayTrack(key,focus=false){
  const item=tracks[key];
  if(!item||!panel)return;
  buttons.forEach(button=>{
    const active=button.dataset.track===key;
    button.setAttribute("aria-selected",active?"true":"false");
    button.tabIndex=active?0:-1;
    if(active&&focus)button.focus();
  });
  panel.setAttribute("aria-labelledby","tab-"+key);
  panel.replaceChildren();
  const number=document.createElement("div");number.className="track-number";number.setAttribute("aria-hidden","true");number.textContent=item.num;
  const copy=document.createElement("div");copy.className="track-copy";
  const tag=document.createElement("span");tag.className="tag";tag.textContent=item.tag;
  const h=document.createElement("h3");h.textContent=item.title;
  const p=document.createElement("p");p.textContent=item.description;
  const meta=document.createElement("div");meta.className="track-meta";
  item.meta.forEach(value=>{const s=document.createElement("span");s.textContent=value;meta.append(s);});
  copy.append(tag,h,p,meta);panel.append(number,copy);
}
buttons.forEach((button,index)=>{
  button.addEventListener("click",()=>displayTrack(button.dataset.track));
  button.addEventListener("keydown",event=>{
    const keys=["ArrowRight","ArrowLeft","Home","End"];
    if(!keys.includes(event.key))return;
    event.preventDefault();
    let to=event.key==="Home"?0:event.key==="End"?buttons.length-1:
      (index+(event.key==="ArrowRight"?1:-1)+buttons.length)%buttons.length;
    displayTrack(buttons[to].dataset.track,true);
  });
});
const toggle=document.getElementById("menu-toggle");
const nav=document.getElementById("site-nav");
if(toggle&&nav){
  toggle.addEventListener("click",()=>{
    const opened=nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded",String(opened));
  });
  nav.querySelectorAll("a").forEach(link=>link.addEventListener("click",()=>{
    nav.classList.remove("is-open");toggle.setAttribute("aria-expanded","false");
  }));
}
