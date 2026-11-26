"""Baselines non génératives J1 : B0-a règle z-score, B0-b Isolation Forest."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

N_NUMERIC = 5


class ZScoreRule:
    """Score = max |z| sur les variables numériques (déjà standardisées sur le train normal)."""
    name = "B0a_zscore"

    def __init__(self, n_numeric: int = N_NUMERIC):
        self.n = n_numeric

    def fit(self, x: np.ndarray) -> "ZScoreRule":
        return self

    def score(self, x: np.ndarray) -> np.ndarray:
        return np.abs(x[:, :self.n]).max(1)


class IForest:
    name = "B0b_isolation_forest"

    def __init__(self, seed: int = 0, n_estimators: int = 200):
        self.model = IsolationForest(n_estimators=n_estimators, random_state=seed)

    def fit(self, x: np.ndarray) -> "IForest":
        self.model.fit(x)
        return self

    def score(self, x: np.ndarray) -> np.ndarray:
        return -self.model.score_samples(x)
