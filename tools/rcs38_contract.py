"""Contrôle strict des fixtures et du contrat UI : pas un test clinique."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "frontend" / "monitoring" / "demo.json"
ALLOWED = {"Site démo A", "Site démo B"}
def validate_fixture(path: Path = DATA) -> dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if x.get("data_mode")!="fictional_demo_only":
        raise ValueError("Refus de données dont la nature fictive n'est pas déclarée")
    for key in ("devices","readings","actions","runs"):
        if not isinstance(x.get(key),list):
            raise ValueError(f"Collection {key} absente")
    for key in ("devices","readings","actions","runs"):
        for record in x[key]:
            if record.get("site") not in ALLOWED:
                raise ValueError("Site non fictif")
            if any(s in record for s in ("patient","patient_id","patient_name","api_key","raw_prompt")):
                raise ValueError("Champ patient, prompt ou secret interdit")
    for record in x["runs"]:
        if record.get("boundary")=="API distante : ND":
            if record.get("energy_kwh") is not None or record.get("co2e_kg") is not None:
                raise ValueError("Énergie distante non observable : utiliser null")
        if not record.get("version") or not record.get("model"):
            raise ValueError("Modèle/version doit être renseigné dans la démo")
    return {k:len(x[k]) for k in ("devices","readings","actions","runs")}

if __name__=="__main__":
    print(validate_fixture())
