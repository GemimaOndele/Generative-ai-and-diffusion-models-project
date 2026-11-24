"""Baseline de détection d'anomalies règles/ML — RCS-55.

Objectif :
- fournir un protocole reproductible (dataset indépendant, split, seed, métriques) ;
- comparer une baseline règles simple à une baseline ML (IsolationForest) ;
- ne pas inventer de résultats réels : les métriques affichées proviennent uniquement
  d'une exécution sur les données chargées/générées localement.

Règle de calibration (anti-fuite de distribution) :
- le ``StandardScaler`` est ajusté sur le TRAIN uniquement ;
- sa moyenne et son écart-type (``scale_``, ddof=0) sont conservés dans
  ``RuleCalibration`` puis appliqués au TEST ;
- aucune statistique n'est recalculée sur le TEST ni sur TRAIN+TEST, et les
  labels du TEST ne servent qu'à l'évaluation.

Usage :
  python experiments/baseline_rules_ml.py --data path/to/dataset.csv --out experiments/results/baseline_rules_ml.json
  python experiments/baseline_rules_ml.py --synthetic --out experiments/results/rcs55_baseline_rules_ml.json

Le mode --synthetic sert uniquement à valider le pipeline (smoke test), pas à prouver
une performance sur données médicales réelles.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


@dataclass
class RunConfig:
    seed: int = 42
    test_size: float = 0.2
    contamination: float = 0.05
    z_threshold: float = 3.0
    data_path: str | None = None
    synthetic: bool = False
    n_samples: int = 2000
    n_features: int = 8


@dataclass(frozen=True)
class RuleCalibration:
    """Statistiques de la baseline règles, estimées sur le train uniquement."""

    means: Tuple[float, ...]
    stds: Tuple[float, ...]
    features: Tuple[str, ...]

    @classmethod
    def fit(cls, X) -> "RuleCalibration":
        scaler = StandardScaler()
        scaler.fit(X)
        stds = np.where(scaler.scale_ == 0.0, 1.0, scaler.scale_)
        n_features = np.asarray(X).shape[1]
        features = tuple(str(c) for c in getattr(X, "columns", [])) or tuple(
            f"f{i + 1}" for i in range(n_features)
        )
        return cls(
            means=tuple(float(v) for v in scaler.mean_),
            stds=tuple(float(v) for v in stds),
            features=features,
        )

    def as_dict(self) -> Dict:
        return {
            "fitted_on": "train_only",
            "features": list(self.features),
            "means": list(self.means),
            "stds": list(self.stds),
            "std_ddof": 0,
        }


def fit_rule_calibration(X_train) -> RuleCalibration:
    """Calibre le z-score de la baseline règles sur le train uniquement."""
    return RuleCalibration.fit(X_train)


def make_synthetic(cfg: RunConfig) -> pd.DataFrame:
    """Génère un dataset synthétique pour smoke test uniquement."""
    rng = np.random.default_rng(cfg.seed)
    n_anom = max(1, int(cfg.n_samples * cfg.contamination))
    n_norm = cfg.n_samples - n_anom
    normal = rng.normal(loc=0.0, scale=1.0, size=(n_norm, cfg.n_features))
    anom = rng.normal(loc=4.0, scale=1.5, size=(n_anom, cfg.n_features))
    X = np.vstack([normal, anom])
    y = np.array([0] * n_norm + [1] * n_anom)
    cols = [f"f{i+1}" for i in range(cfg.n_features)]
    df = pd.DataFrame(X, columns=cols)
    df["label"] = y
    return df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)


def load_dataset(cfg: RunConfig) -> pd.DataFrame:
    if cfg.synthetic:
        return make_synthetic(cfg)
    if not cfg.data_path:
        raise ValueError("--data requis (ou utiliser --synthetic pour smoke test)")
    path = Path(cfg.data_path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet"}:
        return pd.read_parquet(path)
    raise ValueError(f"Format non supporté: {path.suffix}")


def stratified_split(X, y, cfg: RunConfig):
    """Split train/test stratifié et reproductible (même seed, même résultat)."""
    stratify = y if len(np.unique(y)) > 1 else None
    return train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.seed, stratify=stratify
    )


def rule_based_predict(X, calibration: RuleCalibration, z_threshold: float) -> np.ndarray:
    """Anomalie si une feature dépasse ``z_threshold`` en valeur absolue.

    Le z-score est calculé avec les statistiques TRAIN de ``calibration`` ;
    aucune statistique n'est estimée sur les lignes passées ici (TEST).
    """
    values = X.to_numpy(dtype=float) if hasattr(X, "to_numpy") else np.asarray(X, dtype=float)
    means = np.asarray(calibration.means, dtype=float)
    stds = np.asarray(calibration.stds, dtype=float)
    if values.ndim != 2 or values.shape[1] != means.size:
        raise ValueError("Nombre de features incompatible avec la calibration train")
    z = (values - means) / stds
    return (np.abs(z).max(axis=1) > float(z_threshold)).astype(int)


def evaluate(y_true, y_pred) -> Dict:
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix_labels": ["normal", "anomaly"],
        "confusion_matrix": cm,
        "report": classification_report(y_true, y_pred, labels=[0, 1], target_names=["normal", "anomaly"], zero_division=0),
    }


def run(cfg: RunConfig) -> Dict:
    df = load_dataset(cfg)
    if "label" not in df.columns:
        raise ValueError("Le dataset doit contenir une colonne 'label' (0=normal, 1=anomaly).")

    X = df.drop(columns=["label"])
    y = df["label"].astype(int).to_numpy()
    X_train, X_test, y_train, y_test = stratified_split(X, y, cfg)

    # Baseline règles : calibration TRAIN uniquement, application au TEST.
    calibration = fit_rule_calibration(X_train)
    y_pred_rules = rule_based_predict(X_test, calibration, cfg.z_threshold)

    # Baseline ML (IsolationForest) - entraîné sur train sans labels pour rester réaliste.
    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s = scaler.transform(X_test)
    iso = IsolationForest(random_state=cfg.seed, contamination=cfg.contamination)
    iso.fit(X_train_s)
    y_pred_iso = (iso.predict(X_test_s) == -1).astype(int)

    results = {
        "schema": "rcs55_baseline_rules_ml/v1",
        "status": "computed",
        "source": "synthetic_smoke_test" if cfg.synthetic else "dataset",
        "config": asdict(cfg),
        "protocol": {
            "dataset": "dataset indépendant à sélectionner ; --synthetic = smoke test non médical",
            "split": "train/test stratifié",
            "seed": cfg.seed,
            "test_size": cfg.test_size,
            "rule_calibration": (
                "StandardScaler ajusté sur le train uniquement ; moyenne et écart-type "
                "train (ddof=0) appliqués au test, sans recalcul sur le test"
            ),
            "metrics": ["precision", "recall", "f1", "confusion_matrix"],
        },
        "thresholds": {
            "z_threshold": {
                "value": cfg.z_threshold,
                "calibration": "statistiques du z-score calibrées sur le train uniquement",
                "frozen": False,
                "status": "ND (seuil de détection non gelé)",
            },
            "isolation_forest_contamination": {
                "value": cfg.contamination,
                "frozen": False,
                "status": "ND (seuil de détection non gelé)",
            },
            "decision_threshold": "ND (à définir avant campagne)",
        },
        "dataset": {
            "rows": int(len(df)),
            "features": list(X.columns),
            "label_distribution": {str(k): int(v) for k, v in pd.Series(y).value_counts().to_dict().items()},
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        },
        "rules_calibration": calibration.as_dict(),
        "rules_baseline": evaluate(y_test, y_pred_rules),
        "isolation_forest_baseline": evaluate(y_test, y_pred_iso),
        "notes": [
            "Résultats calculés uniquement sur les données chargées/générées lors de cette exécution.",
            "Le mode synthetic est un smoke test, pas une preuve de performance médicale.",
            "Aucun seuil de détection n'est gelé : la valeur de configuration n'est pas un seuil validé.",
            "Aucun résultat ne doit être interprété comme validation clinique.",
        ],
    }
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None, help="CSV/Parquet avec colonne label")
    parser.add_argument("--out", default="experiments/results/baseline_rules_ml.json")
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--contamination", type=float, default=0.05)
    parser.add_argument("--z-threshold", type=float, default=3.0)
    args = parser.parse_args()

    cfg = RunConfig(
        seed=args.seed,
        test_size=args.test_size,
        contamination=args.contamination,
        z_threshold=args.z_threshold,
        data_path=args.data,
        synthetic=args.synthetic,
    )
    results = run(cfg)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps({k: results[k]["f1"] for k in ["rules_baseline", "isolation_forest_baseline"]}, indent=2))


if __name__ == "__main__":
    main()
