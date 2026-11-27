"""J1 — Baselines non génératives vs DDPM (détection d'anomalies par reconstruction) sur AI4I.

Usage :
    python src/run_j1_diffusion.py                 # protocole complet (3 seeds, ~quelques minutes CPU)
    python src/run_j1_diffusion.py --quick         # fumée (1 seed, entraînement court)

Sorties : experiments/results/j1_runs.jsonl, j1_summary.csv, j1_generation.json, j1_config.json
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rcs import RESULTS  # noqa: E402
from rcs.j1.baselines import IForest, ZScoreRule  # noqa: E402
from rcs.j1.data import AI4I_SHA256, NUMERIC, PHYSICS, load_ai4i, make_splits  # noqa: E402
from rcs.j1.diffusion import DDPMConfig, TabularDDPM  # noqa: E402
from rcs.j1.evaluate import evaluate, threshold_at_fpr  # noqa: E402

# G1-A = configuration de référence ; chaque variante change UN seul facteur.
DIFFUSION_VARIANTS = {
    # score « ELBO » : erreur de débruitage moyennée sur n_t pas de temps x k bruits
    "G1-A_elbo_nt10": dict(method="elbo", n_t=10, k=4),                 # référence
    "G1-B_elbo_nt3": dict(method="elbo", n_t=3, k=4),                   # ablation NFE (latence)
    "G1-C_recon_t0=50": dict(method="recon", t0=50, k=4, nfe=None),     # ablation fonction de score
    "G1-D_recon_t0=50_ddim5": dict(method="recon", t0=50, k=4, nfe=5),  # ablation sampler (vs G1-C)
}


def diffusion_score(ddpm, x, seed, method, **kw):
    if method == "elbo":
        return ddpm.score_elbo(x, seed=seed, **kw)
    return ddpm.score(x, seed=seed, **kw)


def nfe_of(kw):
    if kw["method"] == "elbo":
        return kw["n_t"] * kw["k"]
    return (kw["nfe"] or kw["t0"] + 1) * kw["k"]


def timed(fn, *a, **kw):
    t = time.perf_counter()
    out = fn(*a, **kw)
    return out, time.perf_counter() - t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default=str(RESULTS))
    ap.add_argument("--features", choices=["raw", "physics", "both"], default="both")
    args = ap.parse_args()
    seeds = [0] if args.quick else args.seeds
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(max(1, torch.get_num_threads()))

    df = load_ai4i()
    feature_sets = ["raw", "physics"] if args.features == "both" else [args.features]
    all_runs, gens = [], {}
    for fs in feature_sets:
        runs, gen = run_feature_set(df, fs, seeds, args.quick)
        all_runs += runs
        gens[fs] = gen
    save(all_runs, gens, seeds, args.quick, out)


def run_feature_set(df, fs, seeds, quick):
    sp = make_splits(df, fs)
    print(f"=== features={fs} ===")
    print(f"train normal={len(sp.x_train_normal)} val={len(sp.x_val)} (anom={sp.y_val.sum()}) "
          f"test={len(sp.x_test)} (anom={sp.y_test.sum()})")

    runs = []

    def record(name, seed, s_val, s_test, fit_s, score_s, extra=None):
        thr = threshold_at_fpr(s_val, sp.y_val)
        m = evaluate(s_test, sp.y_test, thr, sp.modes_test)
        m.update(model=name, features=fs, seed=seed, fit_seconds=round(fit_s, 3),
                 score_ms_per_1k=round(score_s * 1e6 / len(sp.x_test), 3))
        if extra:
            m.update(extra)
        runs.append(m)
        print(f"{name:28s} seed={seed} PR-AUC={m['pr_auc']:.3f} recall@5%FPR={m['recall_at_thr']:.3f} "
              f"F1={m['f1_at_thr']:.3f} fit={fit_s:.1f}s")

    # B0-a : règle (déterministe)
    zr = ZScoreRule(sp.n_numeric).fit(sp.x_train_normal)
    s_val, _ = timed(zr.score, sp.x_val)
    s_test, dt = timed(zr.score, sp.x_test)
    record(zr.name, 0, s_val, s_test, 0.0, dt)

    gen_report = None
    for seed in seeds:
        ifo, fit_s = timed(IForest(seed).fit, sp.x_train_normal)
        s_val = ifo.score(sp.x_val)
        s_test, dt = timed(ifo.score, sp.x_test)
        record(ifo.name, seed, s_val, s_test, fit_s, dt)

        cfg = DDPMConfig(seed=seed, train_steps=600 if quick else 4000)
        ddpm, fit_s = timed(TabularDDPM(cfg, sp.n_numeric).fit, sp.x_train_normal)
        for vname, kw in DIFFUSION_VARIANTS.items():
            s_val = diffusion_score(ddpm, sp.x_val, seed + 100, **kw)
            s_test, dt = timed(diffusion_score, ddpm, sp.x_test, seed + 200, **kw)
            record(vname, seed, s_val, s_test, fit_s, dt, {"nfe_per_sample": nfe_of(kw)})

        if seed == seeds[0]:
            gen_report = generation_check(ddpm, sp, seed)
    return runs, gen_report


def save(runs, gen_report, seeds, quick, out):
    pd.DataFrame(runs).to_json(out / "j1_runs.jsonl", orient="records", lines=True, force_ascii=False)
    summary = (pd.DataFrame(runs)
               .groupby(["features", "model"])[["pr_auc", "roc_auc", "recall_at_thr", "fpr_test_at_thr", "f1_at_thr",
                                  "recall_TWF", "recall_HDF", "recall_PWF", "recall_OSF", "recall_RNF",
                                  "fit_seconds", "score_ms_per_1k"]]
               .agg(["mean", "std"]).round(4))
    summary.columns = [f"{a}_{b}" for a, b in summary.columns]
    summary.to_csv(out / "j1_summary.csv")
    (out / "j1_generation.json").write_text(json.dumps(gen_report, indent=2), encoding="utf-8")
    (out / "j1_config.json").write_text(json.dumps({
        "dataset": "AI4I 2020 (UCI, CC BY 4.0)", "sha256": AI4I_SHA256,
        "split": "stratifié 60/20/20, seed 42, entraînement sur normaux du train uniquement",
        "threshold_rule": "quantile 95% des scores normaux de validation (FPR cible 5%)",
        "seeds": seeds, "ddpm": DDPMConfig(train_steps=600 if quick else 4000).__dict__,
        "feature_sets": {"raw": NUMERIC, "physics": NUMERIC + PHYSICS},
        "variants": DIFFUSION_VARIANTS, "hardware": platform.processor() or platform.machine(),
        "torch": torch.__version__, "python": platform.python_version(), "quick": quick,
    }, indent=2, default=str), encoding="utf-8")
    print(summary[["pr_auc_mean", "pr_auc_std", "recall_at_thr_mean", "f1_at_thr_mean"]])


def generation_check(ddpm: TabularDDPM, sp, seed: int) -> dict:
    """Preuve de génération : échantillons synthétiques normaux vs réels + contrôle de copie (mémorisation)."""
    from scipy.stats import ks_2samp

    rng = np.random.default_rng(seed)
    n = sp.n_numeric
    cond = sp.x_train_normal[rng.choice(len(sp.x_train_normal), 2000, replace=False), n:]
    gen = ddpm.sample(cond, seed=seed)
    real = sp.x_train_normal[:, :n]
    rep = {"n_generated": len(gen), "features": {}}
    for j, name in enumerate(sp.feature_names[:n]):
        ks = ks_2samp(gen[:, j], real[:, j])
        rep["features"][name] = {
            "real_mean_std": [float(real[:, j].mean() * sp.std[j] + sp.mean[j]), float(real[:, j].std() * sp.std[j])],
            "gen_mean_std": [float(gen[:, j].mean() * sp.std[j] + sp.mean[j]), float(gen[:, j].std() * sp.std[j])],
            "ks_stat": float(ks.statistic),
        }
    # Distance au plus proche voisin : généré->train vs test normal->train (référence)
    from sklearn.neighbors import NearestNeighbors
    nn_ = NearestNeighbors(n_neighbors=1).fit(real)
    d_gen = nn_.kneighbors(gen)[0].ravel()
    test_norm = sp.x_test[sp.y_test == 0][:, :n]
    d_ref = nn_.kneighbors(test_norm)[0].ravel()
    rep["nn_distance_generated_median"] = float(np.median(d_gen))
    rep["nn_distance_real_holdout_median"] = float(np.median(d_ref))
    rep["share_generated_closer_than_1pct_holdout"] = float((d_gen < np.quantile(d_ref, 0.01)).mean())
    rep["examples_original_units"] = (gen[:5] * sp.std + sp.mean).round(2).tolist()
    rep["memorisation_note"] = ("part des générés plus proches du train que le 1er centile des vrais held-out ; "
                                "≈0.01 attendu sans copie, >>0.01 suggère mémorisation")
    return rep


if __name__ == "__main__":
    main()
