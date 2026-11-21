"""RCS-71 / TP03 — Baseline vs diffusion sur 10 cas gelés (mêmes entrées, mêmes critères).

Les 10 cas sont tirés du TEST (split figé seed 42) par une règle déterministe écrite AVANT exécution :
4 normaux typiques, 1 normal « difficile » proche de la frontière HDF, 1 panne par mode (TWF, HDF, PWF, OSF, RNF).
Seuils : quantile 95 % des normaux de validation (jamais le test). Représentation : `raw`.

    python src/run_j1_cases.py
Sorties : experiments/j1_diffusion/test_cases.jsonl (définition des cas) et experiments/results.csv
(format commun du dépôt : case_id,strategy,metric,value,unit,evidence_status,notes)
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rcs.j1.baselines import IForest, ZScoreRule  # noqa: E402
from rcs.j1.data import FAILURE_MODES, SPLIT_SEED, load_ai4i  # noqa: E402
from rcs.j1.diffusion import DDPMConfig, TabularDDPM  # noqa: E402
from rcs.j1.evaluate import threshold_at_fpr  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
import pandas as pd  # noqa: E402
from rcs.j1.data import NUMERIC  # noqa: E402


def frozen_cases(df: pd.DataFrame, i_test: np.ndarray) -> list[dict]:
    t = df.iloc[i_test]
    normal = t[t["Machine failure"] == 0]
    cases = []
    for k, (_, r) in enumerate(normal.head(4).iterrows(), 1):
        cases.append({"id": f"J{k:02d}", "category": "normal_typique", "udi": int(r["UDI"]), "label": 0, "mode": "-"})
    d_t = normal["Process temperature [K]"] - normal["Air temperature [K]"]
    hard = normal[(d_t < 9.0) & (normal["Rotational speed [rpm]"] < 1450)]
    r = hard.iloc[0]
    cases.append({"id": "J05", "category": "normal_difficile (proche frontière HDF)", "udi": int(r["UDI"]),
                  "label": 0, "mode": "-"})
    for k, m in enumerate(FAILURE_MODES, 6):
        r = t[t[m] == 1].iloc[0]
        cases.append({"id": f"J{k:02d}", "category": f"panne_{m}", "udi": int(r["UDI"]), "label": 1, "mode": m})
    return cases


def main() -> None:
    df = load_ai4i()
    y = df["Machine failure"].to_numpy(int)
    idx = np.arange(len(df))
    i_train, i_tmp = train_test_split(idx, test_size=0.4, stratify=y, random_state=SPLIT_SEED)
    i_val, i_test = train_test_split(i_tmp, test_size=0.5, stratify=y[i_tmp], random_state=SPLIT_SEED)
    i_trn = i_train[y[i_train] == 0]

    x_num = df[NUMERIC].to_numpy(float)
    mean, std = x_num[i_trn].mean(0), x_num[i_trn].std(0) + 1e-8
    types = pd.get_dummies(df["Type"]).reindex(columns=["L", "M", "H"], fill_value=0).to_numpy(float)
    x = np.hstack([(x_num - mean) / std, types])

    cases = frozen_cases(df, i_test)
    out_cases = ROOT / "experiments" / "j1_diffusion" / "test_cases.jsonl"
    out_cases.parent.mkdir(parents=True, exist_ok=True)
    with open(out_cases, "w", encoding="utf-8") as f:
        for c in cases:
            row = df[df["UDI"] == c["udi"]].iloc[0]
            c_full = dict(c, entree={k: float(row[k]) for k in NUMERIC} | {"Type": row["Type"]})
            f.write(json.dumps(c_full, ensure_ascii=False) + "\n")
    x_cases = np.stack([x[df.index[df["UDI"] == c["udi"]][0]] for c in cases])

    ddpm = TabularDDPM(DDPMConfig(seed=0)).fit(x[i_trn])
    models = {
        "B0a_zscore": (lambda z: ZScoreRule().score(z)),
        "B0b_isolation_forest": IForest(0).fit(x[i_trn]).score,
        "G1-A_ddpm_elbo_nt10": (lambda z: ddpm.score_elbo(z, n_t=10, k=4, seed=101)),
        "G1-B_ddpm_elbo_nt3": (lambda z: ddpm.score_elbo(z, n_t=3, k=4, seed=101)),
    }
    rows, alerts = [], {}
    note = "AI4I raw, seed 0, seuil = q95 des normaux de validation ; substitut NON médical"
    for name, fn in models.items():
        thr = threshold_at_fpr(fn(x[i_val]), y[i_val])
        t0 = time.perf_counter()
        s = fn(x_cases)
        dt = (time.perf_counter() - t0) * 1000
        for c, sc in zip(cases, s):
            alert = int(sc >= thr)
            alerts[(c["id"], name)] = alert
            base = {"case_id": c["id"], "strategy": name, "evidence_status": "mesuré",
                    "notes": f"{c['category']} ; UDI {c['udi']} ; label {c['label']} ; {note}"}
            for metric, value, unit in (("anomaly_score", round(float(sc), 5), "score"),
                                        ("threshold", round(thr, 5), "score"),
                                        ("alert", alert, "bool"),
                                        ("correct", int(alert == c["label"]), "bool"),
                                        ("latency_batch10", round(dt, 2), "ms")):
                rows.append({"case_id": base["case_id"], "strategy": name, "metric": metric, "value": value,
                             "unit": unit, "evidence_status": "mesuré", "notes": base["notes"]})
    out = ROOT / "experiments" / "results.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "strategy", "metric", "value", "unit", "evidence_status", "notes"])
        w.writeheader()
        w.writerows(rows)
    print("case  category                                  " + "  ".join(m[:12] for m in models))
    for c in cases:
        marks = ["ALERTE" if alerts[(c["id"], m)] else "-" for m in models]
        print(f"{c['id']}  {c['category'][:40]:40s}  " + "  ".join(f"{m:12s}" for m in marks))
    for name in models:
        acc = np.mean([int(alerts[(c["id"], name)] == c["label"]) for c in cases])
        print(f"{name:24s} cas corrects = {acc * 10:.0f}/10")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
