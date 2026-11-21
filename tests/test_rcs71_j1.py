"""RCS-71 — DDPM, baselines et règle de seuil (données jouets, sans téléchargement)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rcs.j1.diffusion import DDPMConfig, TabularDDPM  # noqa: E402
from rcs.j1.evaluate import evaluate, threshold_at_fpr  # noqa: E402



def _toy(n=600, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 5))
    cond = np.eye(3)[rng.integers(0, 3, n)]
    return np.hstack([x, cond])


def test_ddpm_trains_scores_and_samples_deterministically():
    x = _toy()
    m = TabularDDPM(DDPMConfig(train_steps=450, seed=0)).fit(x)
    s1 = m.score_elbo(x[:50], seed=1)
    s2 = m.score_elbo(x[:50], seed=1)
    assert s1.shape == (50,) and np.allclose(s1, s2)
    assert m.score(x[:20], t0=10, k=2, nfe=3).shape == (20,)
    assert m.sample(x[:10, 5:]).shape == (10, 5)
    assert m.loss_history[0] > m.loss_history[-1]


def test_ddpm_flags_obvious_outliers():
    x = _toy(1500)
    m = TabularDDPM(DDPMConfig(train_steps=800, seed=0)).fit(x)
    out = x[:50].copy()
    out[:, :5] += 6.0
    assert m.score_elbo(out).mean() > m.score_elbo(x[:50]).mean()


def test_threshold_is_computed_on_validation_normals_only():
    s = np.r_[np.arange(100), 1000.0]
    y = np.r_[np.zeros(100), 1]
    thr = threshold_at_fpr(s, y, 0.05)
    assert thr < 100
    m = evaluate(np.array([0.0, 200.0]), np.array([0, 1]), thr)
    assert m["recall_at_thr"] == 1.0 and m["fpr_test_at_thr"] == 0.0


def test_results_csv_common_schema_and_ten_cases():
    import csv
    p = Path(__file__).resolve().parents[1] / "experiments" / "results.csv"
    with open(p, encoding="utf-8") as f:
        r = list(csv.DictReader(f))
    assert list(r[0].keys()) == ["case_id", "strategy", "metric", "value", "unit", "evidence_status", "notes"]
    assert len({x["case_id"] for x in r}) == 10
    assert {x["evidence_status"] for x in r} == {"mesuré"}
    assert {"B0a_zscore", "G1-A_ddpm_elbo_nt10"} <= {x["strategy"] for x in r}
