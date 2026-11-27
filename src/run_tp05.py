"""TP05 — FinOps & Green AI : agrège les traces TP04 (+ levier) en coût et CO2e par tâche réussie.

    python src/run_tp05.py
Entrées : experiments/results/tp04_local_{summary,energy}.csv et tp05_lever_{summary,energy}.csv (si présents).
Sortie  : experiments/results/rcs82_tp05_mesures.csv (une ligne par variante/stratégie, avec statut de preuve).

Hypothèses (modifiables ci-dessous, à dater et sourcer avant le rendu final) :
- prix de l'électricité ELEC_EUR_PER_KWH : HYPOTHÈSE (ordre de grandeur tarif résidentiel FR) ;
- PUE = 1,0 : exécution sur poste local (pas de datacenter) ;
- intensité carbone : celle utilisée par CodeCarbon pour la France (mode hors-ligne) ;
- coût API = 0 € (modèles ouverts exécutés localement) — une projection API exige un tarif fournisseur daté (ND ici).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcs import RESULTS  # noqa: E402

ELEC_EUR_PER_KWH = 0.25        # HYPOTHÈSE, à remplacer par le tarif réel daté
PUE = 1.0
MONTHLY_VOLUME = 2_000         # HYPOTHÈSE : questions/mois d'un service biomédical pilote


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_rows(results: Path = RESULTS) -> list[dict]:
    rows = []
    for prefix in ("tp04_local", "tp05_lever"):
        summ = read(results / f"{prefix}_summary.csv")
        energy = {(e["variant"], e["strategy"]): e for e in read(results / f"{prefix}_energy.csv")}
        for s in summ:
            n = int(s["n"])
            ok = round(float(s["quality"]) * n)
            e = energy.get((s["variant"], s["strategy"]))
            kwh = float(e["energy_kwh"]) * PUE if e else None
            co2 = float(e["co2e_kg"]) if e else None
            elec_eur = kwh * ELEC_EUR_PER_KWH if kwh is not None else None
            rows.append({
                "source": prefix, "variant": s["variant"], "strategy": s["strategy"],
                "cas": n, "taches_reussies": ok, "qualite": s["quality"],
                "appels_llm": s["calls"], "tokens_in": s["input_tokens"], "tokens_out": s["output_tokens"],
                "p95_ms": s["p95_ms"], "erreurs": s["errors"],
                "energie_kwh": f"{kwh:.6f}" if kwh is not None else "ND",
                "co2e_g": f"{co2 * 1000:.3f}" if co2 is not None else "ND",
                "cout_api_eur": "0 (local)",
                "cout_elec_eur": f"{elec_eur:.6f}" if elec_eur is not None else "ND",
                "cout_par_succes_eur": f"{elec_eur / ok:.6f}" if elec_eur is not None and ok else "ND",
                "co2e_g_par_succes": f"{co2 * 1000 / ok:.3f}" if co2 is not None and ok else "ND",
                "projection_mensuelle_elec_eur": (f"{elec_eur / n * MONTHLY_VOLUME:.4f}"
                                                  if elec_eur is not None else "ND"),
                "statut_energie": "estimé CodeCarbon (TDP/RAM, hors-ligne FRA)" if e else "non mesuré",
                "statut_cout": "calcul = kWh estimés × tarif HYPOTHÈSE",
            })
    return rows


def main() -> None:
    rows = build_rows()
    out = RESULTS / "rcs82_tp05_mesures.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['variant']:9s} {r['strategy']:14s} Q={r['qualite']:5s} succès={r['taches_reussies']:2d} "
              f"kWh={r['energie_kwh']:>9s} gCO2e={r['co2e_g']:>7s} €/succès={r['cout_par_succes_eur']:>9s} "
              f"p95={r['p95_ms']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
