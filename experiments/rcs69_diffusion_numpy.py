"""RCS-69 — DDPM denoiser entraîné sur signaux SYNTHÉTIQUES, non médicaux.

NumPy CPU uniquement. MLP apprend à prédire le bruit epsilon de q(x_t|x_0).
Un échantillonneur inverse DDPM est exécuté. Baseline MAD et diffusion sont
évaluées sur le même TEST indépendant après seuil sur validation normale.
Aucune supériorité clinique ou transférabilité n'est démontrée.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

D, T = 24, 24
BETA = np.linspace(0.02, 0.16, T)
ALPHA = 1.0 - BETA
ALPHA_BAR = np.cumprod(ALPHA)


def synthetic_signals(rng: np.random.Generator, n: int, anomaly: bool = False) -> np.ndarray:
    grid = np.linspace(0, 2 * np.pi, D, endpoint=False)
    phase = rng.uniform(0, 2 * np.pi, (n, 1))
    amplitude = rng.uniform(0.7, 1.3, (n, 1))
    signals = amplitude * np.sin(grid[None, :] + phase)
    signals += rng.normal(0, 0.09, (n, D))
    if anomaly:
        for i in range(n):
            idx = int(rng.integers(0, D))
            signals[i, idx] += (1 if i % 2 else -1) * float(rng.uniform(1.5, 2.8))
            if i % 3 == 0:
                signals[i, (idx + 1) % D] += 1.25
    return signals


def features(x: np.ndarray, steps: np.ndarray) -> np.ndarray:
    t = (steps / T).reshape(-1, 1)
    return np.concatenate((x, np.sin(2 * np.pi * t), np.cos(2 * np.pi * t)), axis=1)


class Denoiser:
    """Réseau epsilon: MLP à une couche cachée, paramètres entraînés par Adam."""
    def __init__(self, seed: int, hidden: int = 48):
        rng = np.random.default_rng(seed)
        self.params = {
            "w1": rng.normal(0, 0.08, (D + 2, hidden)),
            "b1": np.zeros(hidden),
            "w2": rng.normal(0, 0.08, (hidden, D)),
            "b2": np.zeros(D),
        }
        self.m = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.v = {key: np.zeros_like(value) for key, value in self.params.items()}
        self.n_updates = 0

    def predict(self, x: np.ndarray, steps: np.ndarray) -> np.ndarray:
        h = np.tanh(features(x, steps) @ self.params["w1"] + self.params["b1"])
        return h @ self.params["w2"] + self.params["b2"]

    def train(self, normals: np.ndarray, rng: np.random.Generator, updates: int = 250,
              batch_size: int = 64, lr: float = 0.005) -> list[float]:
        if normals.ndim != 2 or normals.shape[1] != D or len(normals) < 20:
            raise ValueError("Matrice de signaux normaux insuffisante")
        if updates < 1 or batch_size < 1 or lr <= 0:
            raise ValueError("Paramètres d'entraînement invalides")
        losses = []
        for _ in range(updates):
            clean = normals[rng.integers(0, len(normals), batch_size)]
            steps = rng.integers(0, T, batch_size)
            eps = rng.normal(size=clean.shape)
            ab = ALPHA_BAR[steps, None]
            noisy = np.sqrt(ab) * clean + np.sqrt(1-ab) * eps
            x = features(noisy, steps)
            h = np.tanh(x @ self.params["w1"] + self.params["b1"])
            predicted = h @ self.params["w2"] + self.params["b2"]
            err = predicted - eps
            loss = float(np.mean(err**2))
            if not np.isfinite(loss):
                raise ArithmeticError("Divergence de l'entraînement")
            de = 2 * err / err.size
            grads = {"w2": h.T @ de, "b2": de.sum(axis=0)}
            dh = (de @ self.params["w2"].T) * (1 - h**2)
            grads.update(w1=x.T @ dh, b1=dh.sum(axis=0))
            self.n_updates += 1
            for key, grad in grads.items():
                self.m[key] = .9 * self.m[key] + .1 * grad
                self.v[key] = .999 * self.v[key] + .001 * grad**2
                mhat = self.m[key] / (1 - .9**self.n_updates)
                vhat = self.v[key] / (1 - .999**self.n_updates)
                self.params[key] -= lr * mhat / (np.sqrt(vhat)+1e-8)
            losses.append(loss)
        return losses

    def sample(self, rng: np.random.Generator, n: int = 3) -> np.ndarray:
        """DDPM sampler inverse : échantillons synthétiques, non biologiques."""
        x = rng.normal(size=(n, D))
        for t in reversed(range(T)):
            predicted = self.predict(x, np.full(n, t, dtype=np.int64))
            mean = (x - BETA[t] * predicted / np.sqrt(1 - ALPHA_BAR[t])) / np.sqrt(ALPHA[t])
            if t:
                variance = BETA[t] * (1-ALPHA_BAR[t-1]) / (1-ALPHA_BAR[t])
                x = mean + np.sqrt(variance) * rng.normal(size=x.shape)
            else:
                x = mean
        return x

    def scores(self, rng: np.random.Generator, signals: np.ndarray,
               t: int = 8, repeats: int = 4) -> np.ndarray:
        if not 0 <= t < T or repeats < 1:
            raise ValueError("Configuration d'évaluation invalide")
        scores = np.zeros(len(signals))
        for _ in range(repeats):
            noise = rng.normal(size=signals.shape)
            noisy = np.sqrt(ALPHA_BAR[t])*signals + np.sqrt(1-ALPHA_BAR[t])*noise
            eps_pred = self.predict(noisy, np.full(len(signals), t))
            x0_hat = (noisy - np.sqrt(1-ALPHA_BAR[t])*eps_pred) / np.sqrt(ALPHA_BAR[t])
            scores += np.mean((signals-x0_hat)**2, axis=1)
        return scores / repeats


def mad_scores(train: np.ndarray, x: np.ndarray) -> np.ndarray:
    centre = np.median(train, axis=0)
    scale = np.maximum(1.4826*np.median(np.abs(train-centre),axis=0), .12)
    return np.mean(((x-centre)/scale)**2, axis=1)


def metrics(y: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    predicted = scores > threshold
    tp = int(np.sum((y == 1) & predicted))
    fp = int(np.sum((y == 0) & predicted))
    tn = int(np.sum((y == 0) & ~predicted))
    fn = int(np.sum((y == 1) & ~predicted))
    precision = tp/(tp+fp) if tp+fp else None
    recall = tp/(tp+fn) if tp+fn else None
    f1 = 2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else None
    return {"threshold_validation_normal_95pct":round(float(threshold),6),
            "TP":tp,"FP":fp,"TN":tn,"FN":fn,
            "precision":round(precision,4) if precision is not None else None,
            "recall":round(recall,4) if recall is not None else None,
            "f1":round(f1,4) if f1 is not None else None,
            "false_alarm_rate":round(fp/(fp+tn),4) if fp+tn else None}


def experiment(seed: int = 42, updates: int = 250) -> dict:
    if updates < 1:
        raise ValueError("Un débruiteur doit être réellement entraîné")
    rng = np.random.default_rng(seed)
    train = synthetic_signals(rng, 320)
    valid_normal = synthetic_signals(rng, 96)
    normal_test = synthetic_signals(rng, 64)
    abnormal_test = synthetic_signals(rng, 64, anomaly=True)
    test = np.concatenate((normal_test, abnormal_test))
    labels = np.concatenate((np.zeros(64, dtype=np.int8), np.ones(64,dtype=np.int8)))
    model = Denoiser(seed+1)
    begin = time.perf_counter()
    losses = model.train(train, np.random.default_rng(seed+2), updates=updates)
    elapsed = time.perf_counter()-begin
    diff_valid = model.scores(np.random.default_rng(seed+3), valid_normal)
    diff_test = model.scores(np.random.default_rng(seed+4), test)
    baseline_valid = mad_scores(train, valid_normal)
    baseline_test = mad_scores(train, test)
    generated = model.sample(np.random.default_rng(seed+5), n=3)
    return {
        "scope":"synthetic_signal_research_only_not_medical",
        "training_method":"learned_epsilon_MLP_Adam_DDPM_reverse_sampler",
        "scientific_status":"illustrative_experiment_not_clinical_validation",
        "dataset_source":"generated_sine_signals_in_code",
        "dataset_sha256":hashlib.sha256(train.tobytes()).hexdigest(),
        "seed":seed,"numpy_version":np.__version__,
        "signal_length":D,"diffusion_timesteps":T,"train_updates":updates,
        "train_normal":len(train),"validation_normal":len(valid_normal),
        "test_normal":len(normal_test),"test_anomaly":len(abnormal_test),
        "train_loss_start":round(losses[0],6),"train_loss_end":round(losses[-1],6),
        "training_runtime_seconds":round(elapsed,3),
        "baseline_MAD":metrics(labels,baseline_test,float(np.quantile(baseline_valid,.95))),
        "learned_diffusion_denoiser":metrics(labels,diff_test,float(np.quantile(diff_valid,.95))),
        "generated_samples_count":len(generated),
        "sample_finite":bool(np.isfinite(generated).all()),
        "limitations":["All signals and labels artificial; no clinical transfer.",
                       "No superiority asserted beyond this synthetic fixture.",
                       "Thresholds fixed on independent validation normals.",
                       "No energy or API cost measurements."]
    }


def main():
    parser=argparse.ArgumentParser(description="RCS-69 — DDPM synthétique reproductible")
    parser.add_argument("--seed",type=int,default=42)
    parser.add_argument("--updates",type=int,default=250)
    parser.add_argument("--json",type=Path)
    a=parser.parse_args()
    result=experiment(a.seed,a.updates)
    payload=json.dumps(result,ensure_ascii=False,indent=2)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(payload+"\n",encoding="utf-8")
    print(payload)


if __name__=="__main__":
    main()
