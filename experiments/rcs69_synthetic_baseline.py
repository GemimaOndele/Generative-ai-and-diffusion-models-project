"""DÉMONSTRATION SYNTHÉTIQUE de baseline MAD pour maintenance (RCS-69).

Ne démontre PAS une performance sur des dispositifs médicaux, ni un
entraînement/débruitage de diffusion. Valeurs artificielles de tests unitaires.
"""
from __future__ import annotations
import json
import statistics


def median_mad_threshold(normal_training: list[float], multiplier: float = 4.0) -> tuple[float, float]:
    if len(normal_training) < 5 or multiplier <= 0:
        raise ValueError("Il faut un entraînement normal suffisant et un multiplicateur positif")
    centre = statistics.median(normal_training)
    mad = statistics.median([abs(x - centre) for x in normal_training])
    # 1.4826 estime l'écart-type pour une distribution normale ; solution de repli
    # seulement destinée à démontrer le calcul sur cette fixture synthétique.
    threshold = max(1.4826 * mad * multiplier, 0.25)
    return centre, threshold


def evaluate_synthetic_demo() -> dict:
    train = [9.8, 9.9, 10.0, 10.1, 10.2] * 4
    test = [10.0, 9.9, 10.1, 10.0, 9.8, 12.0, 10.2, 8.0, 10.0, 9.9]
    labels = [0, 0, 0, 0, 0, 1, 0, 1, 0, 0]  # étiquettes ajoutées artificiellement
    centre, limit = median_mad_threshold(train)
    preds = [int(abs(x - centre) > limit) for x in test]
    tp = sum(p == y == 1 for p, y in zip(preds, labels))
    fp = sum(p == 1 and y == 0 for p, y in zip(preds, labels))
    fn = sum(p == 0 and y == 1 for p, y in zip(preds, labels))
    return {
        "dataset": "synthetic_fixture_not_medical",
        "baseline": "median_abs_deviation_only",
        "n_train_normal": len(train),
        "n_test": len(test),
        "threshold": limit,
        "tp": tp, "fp": fp, "fn": fn,
        "precision_demo": tp / (tp + fp) if tp + fp else None,
        "recall_demo": tp / (tp + fn) if tp + fn else None,
        "diffusion_model": "not_trained_or_evaluated",
        "transfer_to_medical_devices": "not_validated",
    }


if __name__ == "__main__":
    print(json.dumps(evaluate_synthetic_demo(), ensure_ascii=False, indent=2))
