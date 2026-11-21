"""DDPM tabulaire conditionnel (CPU) pour la détection d'anomalies par reconstruction.

Principe (inspiré de la littérature diffusion-reconstruction, cf. PhysDiff [S07], DDPM Ho et al. 2020) :
1. On entraîne un DDPM (prédiction du bruit ε) sur les observations NORMALES uniquement,
   conditionné par le type de produit (one-hot L/M/H).
2. Pour scorer x0 : on le bruite jusqu'à t0 (q(x_t0|x0)), puis on débruite jusqu'à 0.
   Le modèle « ramène » vers la variété normale ; l'erreur ||x0 - x̂0||² est le score d'anomalie.
3. Moyenne sur K tirages de bruit pour réduire la variance.

Facteurs d'ablation (UN à la fois) : t0 (niveau de bruit), NFE (pas DDIM), K.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, asdict

import numpy as np
import torch
from torch import nn

N_NUMERIC = 5
N_COND = 3


@dataclass
class DDPMConfig:
    T: int = 100
    beta_start: float = 1e-4
    beta_end: float = 0.02
    hidden: int = 128
    train_steps: int = 4000
    batch_size: int = 256
    lr: float = 1e-3
    seed: int = 0


def timestep_embedding(t: torch.Tensor, dim: int = 32) -> torch.Tensor:
    half = dim // 2
    freqs = torch.exp(-math.log(10000) * torch.arange(half, dtype=torch.float32) / half)
    args = t.float()[:, None] * freqs[None]
    return torch.cat([torch.sin(args), torch.cos(args)], dim=1)


class EpsMLP(nn.Module):
    def __init__(self, hidden: int = 128, n_numeric: int = N_NUMERIC):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_numeric + N_COND + 32, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden), nn.SiLU(),
            nn.Linear(hidden, n_numeric),
        )

    def forward(self, x_t, t, cond):
        return self.net(torch.cat([x_t, cond, timestep_embedding(t)], dim=1))


class TabularDDPM:
    name = "G1_ddpm"

    def __init__(self, cfg: DDPMConfig | None = None, n_numeric: int = N_NUMERIC):
        self.cfg = cfg or DDPMConfig()
        self.n = n_numeric
        torch.manual_seed(self.cfg.seed)
        np.random.seed(self.cfg.seed)
        self.betas = torch.linspace(self.cfg.beta_start, self.cfg.beta_end, self.cfg.T)
        self.alphas = 1.0 - self.betas
        self.abar = torch.cumprod(self.alphas, dim=0)
        self.model = EpsMLP(self.cfg.hidden, n_numeric)
        self.train_seconds = None
        self.loss_history: list[float] = []

    # ---------- entraînement ----------
    def fit(self, x: np.ndarray) -> "TabularDDPM":
        g = torch.Generator().manual_seed(self.cfg.seed)
        data = torch.tensor(x, dtype=torch.float32)
        opt = torch.optim.Adam(self.model.parameters(), lr=self.cfg.lr)
        t_start = time.perf_counter()
        self.model.train()
        for step in range(self.cfg.train_steps):
            idx = torch.randint(0, len(data), (self.cfg.batch_size,), generator=g)
            batch = data[idx]
            x0, cond = batch[:, :self.n], batch[:, self.n:]
            t = torch.randint(0, self.cfg.T, (len(batch),), generator=g)
            eps = torch.randn(x0.shape, generator=g)
            ab = self.abar[t][:, None]
            x_t = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
            loss = ((self.model(x_t, t, cond) - eps) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            if step % 200 == 0:
                self.loss_history.append(loss.item())
        self.train_seconds = time.perf_counter() - t_start
        self.model.eval()
        return self

    # ---------- échantillonnage ----------
    @torch.no_grad()
    def _ancestral(self, x_t, cond, t_from: int):
        for t in range(t_from, -1, -1):
            tt = torch.full((len(x_t),), t, dtype=torch.long)
            eps = self.model(x_t, tt, cond)
            a, ab, b = self.alphas[t], self.abar[t], self.betas[t]
            mean = (x_t - b / (1 - ab).sqrt() * eps) / a.sqrt()
            if t > 0:
                var = b * (1 - self.abar[t - 1]) / (1 - ab)
                x_t = mean + var.sqrt() * torch.randn_like(x_t)
            else:
                x_t = mean
        return x_t

    @torch.no_grad()
    def _ddim(self, x_t, cond, t_from: int, nfe: int):
        """DDIM déterministe (eta=0) avec exactement `nfe` évaluations du réseau."""
        ts = np.linspace(t_from, 0, nfe + 1).round().astype(int)
        pairs = list(zip(ts[:-1], ts[1:]))
        for i, (t, t_prev) in enumerate(pairs):
            tt = torch.full((len(x_t),), int(t), dtype=torch.long)
            eps = self.model(x_t, tt, cond)
            ab = self.abar[t]
            x0_hat = (x_t - (1 - ab).sqrt() * eps) / ab.sqrt()
            if i == len(pairs) - 1:
                return x0_hat
            ab_prev = self.abar[t_prev]
            x_t = ab_prev.sqrt() * x0_hat + (1 - ab_prev).sqrt() * eps
        return x_t

    @torch.no_grad()
    def score(self, x: np.ndarray, t0: int = 20, k: int = 8, nfe: int | None = None,
              seed: int = 123) -> np.ndarray:
        """Erreur de reconstruction moyenne. nfe=None => ancestral complet (t0+1 évaluations)."""
        g = torch.Generator().manual_seed(seed)
        data = torch.tensor(x, dtype=torch.float32)
        x0, cond = data[:, :self.n], data[:, self.n:]
        ab = self.abar[t0]
        errs = torch.zeros(len(x0))
        torch.manual_seed(seed)
        for _ in range(k):
            eps = torch.randn(x0.shape, generator=g)
            x_t = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
            x_hat = self._ancestral(x_t, cond, t0) if nfe is None else self._ddim(x_t, cond, t0, nfe)
            errs += ((x_hat - x0) ** 2).mean(1)
        return (errs / k).numpy()

    @torch.no_grad()
    def score_elbo(self, x: np.ndarray, n_t: int = 10, k: int = 4, seed: int = 123) -> np.ndarray:
        """Score « vraisemblance » : erreur de débruitage ||ε - ε_θ(x_t, t)||² moyennée sur une grille
        de t et k bruits (approximation non pondérée de l'ELBO DDPM ; Ho et al. 2020, éq. 14)."""
        g = torch.Generator().manual_seed(seed)
        data = torch.tensor(x, dtype=torch.float32)
        x0, cond = data[:, :self.n], data[:, self.n:]
        ts = np.linspace(0, self.cfg.T - 1, n_t).round().astype(int)
        errs = torch.zeros(len(x0))
        for t in ts:
            ab = self.abar[t]
            tt = torch.full((len(x0),), int(t), dtype=torch.long)
            for _ in range(k):
                eps = torch.randn(x0.shape, generator=g)
                x_t = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
                errs += ((self.model(x_t, tt, cond) - eps) ** 2).mean(1)
        return (errs / (len(ts) * k)).numpy()

    @torch.no_grad()
    def sample(self, cond: np.ndarray, seed: int = 7) -> np.ndarray:
        """Génère des observations normales synthétiques (espace standardisé)."""
        torch.manual_seed(seed)
        c = torch.tensor(cond, dtype=torch.float32)
        x_T = torch.randn(len(c), self.n)
        return self._ancestral(x_T, c, self.cfg.T - 1).numpy()

    def config(self) -> dict:
        return asdict(self.cfg)
