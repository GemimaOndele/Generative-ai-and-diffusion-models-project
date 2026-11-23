"""Baseline de détection d'anomalies règles/ML — RCS-55.

Objectif :
- fournir un protocole reproductible (dataset, split, seed, métriques) ;
- comparer une baseline règles simple à une baseline ML (IsolationForest) ;
- ne pas inventer de résultats réels : les métriques affichées proviennent uniquement
  d'une exécution sur les données chargées/générées localement.

Usage :
  python experiments/baseline_rules_ml.py --data path/to/dataset.csv --out experiments/results/baseline_rules_ml.json
  python experiments/baseline_rules_ml.py --synthetic --out experiments/results/baseline_rules_ml_synthetic.json

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


def rule_based_predict(X: pd.DataFrame, z_threshold: float) -> np.ndarray:
    """Baseline règles: anomalie si une feature dépasse z_threshold en valeur absolue."""
    z = (X - X.mean()) / (X.std(ddof=0).replace(0, 1))
    return (z.abs().max(axis=1) > z_threshold).astype(int).to_numpy()


def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
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
    # Split stratifié reproductible
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=cfg.test_size, random_state=cfg.seed, stratify=y if len(np.unique(y)) > 1 else None
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    X_test_df = pd.DataFrame(X_test_s, columns=X.columns)

    # Baseline règles
    y_pred_rules = rule_based_predict(X_test_df, cfg.z_threshold)

    # Baseline ML (IsolationForest) - entraîné sur train sans labels pour rester réaliste
    iso = IsolationForest(random_state=cfg.seed, contamination=cfg.contamination)
    iso.fit(X_train_s)
    y_pred_iso = (iso.predict(X_test_s) == -1).astype(int)

    results = {
        "config": asdict(cfg),
        "dataset": {
            "rows": int(len(df)),
            "features": list(X.columns),
            "label_distribution": {str(k): int(v) for k, v in pd.Series(y).value_counts().to_dict().items()},
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
        },
        "rules_baseline": evaluate(y_test, y_pred_rules),
        "isolation_forest_baseline": evaluate(y_test, y_pred_iso),
        "notes": [
            "Résultats calculés uniquement sur les données chargées/générées lors de cette exécution.",
            "Le mode synthetic est un smoke test, pas une preuve de performance médicale.",
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
