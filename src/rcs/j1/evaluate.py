"""Métriques J1 : PR-AUC, ROC-AUC, rappel à FPR fixé (seuil choisi sur VALIDATION), F1, par mode de panne."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, f1_score

TARGET_FPR = 0.05


def threshold_at_fpr(scores_val: np.ndarray, y_val: np.ndarray, fpr: float = TARGET_FPR) -> float:
    """Seuil = quantile (1-fpr) des scores des NORMAUX de validation (jamais le test)."""
    return float(np.quantile(scores_val[y_val == 0], 1 - fpr))


def evaluate(scores_test: np.ndarray, y_test: np.ndarray, thr: float,
             modes_test: pd.DataFrame | None = None) -> dict:
    pred = (scores_test >= thr).astype(int)
    tp = int(((pred == 1) & (y_test == 1)).sum())
    fp = int(((pred == 1) & (y_test == 0)).sum())
    out = {
        "pr_auc": float(average_precision_score(y_test, scores_test)),
        "roc_auc": float(roc_auc_score(y_test, scores_test)),
        "recall_at_thr": tp / max(1, int((y_test == 1).sum())),
        "fpr_test_at_thr": fp / max(1, int((y_test == 0).sum())),
        "f1_at_thr": float(f1_score(y_test, pred, zero_division=0)),
        "n_alerts": int(pred.sum()),
        "threshold": thr,
    }
    if modes_test is not None:
        for m in modes_test.columns:
            mask = modes_test[m].to_numpy() == 1
            out[f"recall_{m}"] = float(pred[mask].mean()) if mask.any() else float("nan")
            out[f"n_{m}"] = int(mask.sum())
    return out
