"""Chargement AI4I et splits figés pour J1.

AVERTISSEMENT : AI4I est un jeu SYNTHÉTIQUE industriel (fraiseuse), utilisé comme substitut
méthodologique. Aucune validité médicale n'est revendiquée ; l'ordre des lignes n'est pas une
vraie temporalité, d'où un split aléatoire stratifié (pas de fenêtres temporelles).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from rcs import DATA_RAW

NUMERIC = ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]",
           "Torque [Nm]", "Tool wear [min]"]
FAILURE_MODES = ["TWF", "HDF", "PWF", "OSF", "RNF"]
SPLIT_SEED = 42  # figé : le test ne change jamais entre expériences
AI4I_SHA256 = "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"


@dataclass
class Splits:
    x_train_normal: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    modes_test: pd.DataFrame
    feature_names: list[str]
    mean: np.ndarray
    std: np.ndarray
    n_numeric: int


def load_ai4i(path: str | Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else DATA_RAW / "ai4i2020.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} absent : lancer `python scripts/download_ai4i.py`")
    return pd.read_csv(path, encoding="utf-8-sig")


PHYSICS = ["delta_T [K]", "power [W]", "strain [min.Nm]"]


def numeric_features(df: pd.DataFrame, features: str = "raw") -> tuple[np.ndarray, list[str]]:
    """raw = 5 mesures brutes ; physics = brutes + 3 grandeurs dérivées (connaissance métier explicite :
    écart thermique, puissance mécanique, usure x couple). Les labels ne sont PAS utilisés."""
    x = df[NUMERIC].to_numpy(dtype=np.float64)
    if features == "raw":
        return x, list(NUMERIC)
    if features != "physics":
        raise ValueError(features)
    d_t = df["Process temperature [K]"] - df["Air temperature [K]"]
    power = df["Torque [Nm]"] * df["Rotational speed [rpm]"] * 2 * np.pi / 60
    strain = df["Tool wear [min]"] * df["Torque [Nm]"]
    extra = np.stack([d_t, power, strain], axis=1).astype(np.float64)
    return np.hstack([x, extra]), list(NUMERIC) + PHYSICS


def make_splits(df: pd.DataFrame, features: str = "raw") -> Splits:
    x_num, num_names = numeric_features(df, features)
    types = pd.get_dummies(df["Type"]).reindex(columns=["L", "M", "H"], fill_value=0).to_numpy(np.float64)
    y = df["Machine failure"].to_numpy(dtype=int)
    idx = np.arange(len(df))
    i_train, i_tmp = train_test_split(idx, test_size=0.4, stratify=y, random_state=SPLIT_SEED)
    i_val, i_test = train_test_split(i_tmp, test_size=0.5, stratify=y[i_tmp], random_state=SPLIT_SEED)

    i_train_normal = i_train[y[i_train] == 0]  # apprentissage du comportement NORMAL uniquement
    mean = x_num[i_train_normal].mean(0)
    std = x_num[i_train_normal].std(0) + 1e-8
    z = (x_num - mean) / std
    x = np.hstack([z, types])
    names = num_names + ["Type_L", "Type_M", "Type_H"]
    return Splits(x[i_train_normal], x[i_val], y[i_val], x[i_test], y[i_test],
                  df.iloc[i_test][FAILURE_MODES].reset_index(drop=True), names, mean, std, len(num_names))
