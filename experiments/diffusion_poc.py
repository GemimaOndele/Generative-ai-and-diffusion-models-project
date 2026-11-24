"""POC diffusion pour séries temporelles — RCS-57 / RCS-70.

But : fournir une chaîne minimale reproductible (q_sample/bruitage, modèle de débruitage,
boucle d'entraînement smoke test, échantillonnage/reconstruction, logs et config).
Ce script ne prétend pas fournir une preuve clinique ou un résultat de détection validé.

Usage (smoke test synthétique) :
  python experiments/diffusion_poc.py --synthetic --epochs 2 --out experiments/results/diffusion_poc.json

Prérequis : torch, numpy. Le mode --synthetic génère des signaux sinusoïdaux + bruit.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "PyTorch est requis pour experiments/diffusion_poc.py. "
        "Installez-le puis relancez. Erreur: " + str(exc)
    )


@dataclass
class DiffusionConfig:
    seed: int = 42
    seq_len: int = 64
    channels: int = 1
    n_samples: int = 512
    batch_size: int = 32
    epochs: int = 5
    lr: float = 1e-3
    timesteps: int = 100
    beta_start: float = 1e-4
    beta_end: float = 0.02
    device: str = "cpu"
    synthetic: bool = False
    out: str = "experiments/results/diffusion_poc.json"


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_synthetic_signals(cfg: DiffusionConfig) -> torch.Tensor:
    """Signaux synthétiques pour smoke test : sinusoïdes + bruit."""
    rng = np.random.default_rng(cfg.seed)
    t = np.linspace(0, 4 * np.pi, cfg.seq_len)
    signals = []
    for _ in range(cfg.n_samples):
        amp = rng.uniform(0.5, 1.5)
        freq = rng.uniform(0.8, 1.2)
        phase = rng.uniform(0, 2 * np.pi)
        noise = rng.normal(0, 0.05, size=cfg.seq_len)
        s = amp * np.sin(freq * t + phase) + noise
        signals.append(s)
    arr = np.stack(signals).astype(np.float32)[:, None, :]  # [N, C, L]
    # normalisation simple
    arr = (arr - arr.mean()) / (arr.std() + 1e-6)
    return torch.from_numpy(arr)


class SinusoidalPosEmb(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        device = t.device
        half = self.dim // 2
        emb = math.log(10000) / (half - 1)
        emb = torch.exp(torch.arange(half, device=device) * -emb)
        emb = t[:, None].float() * emb[None, :]
        return torch.cat([emb.sin(), emb.cos()], dim=-1)


class SmallDenoiser(nn.Module):
    """Petit réseau 1D pour smoke test (pas un modèle SOTA)."""

    def __init__(self, channels: int, hidden: int = 32, time_dim: int = 32):
        super().__init__()
        self.time_mlp = nn.Sequential(SinusoidalPosEmb(time_dim), nn.Linear(time_dim, hidden), nn.SiLU())
        self.net = nn.Sequential(
            nn.Conv1d(channels + hidden, hidden, 3, padding=1),
            nn.SiLU(),
            nn.Conv1d(hidden, hidden, 3, padding=1),
            nn.SiLU(),
            nn.Conv1d(hidden, channels, 3, padding=1),
        )

    def forward(self, x: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        temb = self.time_mlp(t)[:, :, None].expand(-1, -1, x.shape[-1])
        h = torch.cat([x, temb], dim=1)
        return self.net(h)


class DiffusionSchedule:
    def __init__(self, cfg: DiffusionConfig, device: torch.device):
        self.T = cfg.timesteps
        beta = torch.linspace(cfg.beta_start, cfg.beta_end, cfg.timesteps, device=device)
        alpha = 1.0 - beta
        alpha_bar = torch.cumprod(alpha, dim=0)
        self.beta = beta
        self.alpha = alpha
        self.alpha_bar = alpha_bar

    def q_sample(self, x0: torch.Tensor, t: torch.Tensor, noise: torch.Tensor) -> torch.Tensor:
        a = self.alpha_bar[t].view(-1, 1, 1)
        return a.sqrt() * x0 + (1 - a).sqrt() * noise


@torch.no_grad()
def p_sample_loop(model: nn.Module, sched: DiffusionSchedule, shape, device: torch.device) -> torch.Tensor:
    x = torch.randn(shape, device=device)
    for i in reversed(range(sched.T)):
        t = torch.full((shape[0],), i, device=device, dtype=torch.long)
        pred_noise = model(x, t)
        a = sched.alpha[i]
        ab = sched.alpha_bar[i]
        beta = sched.beta[i]
        x = (1 / a.sqrt()) * (x - beta / (1 - ab).sqrt() * pred_noise)
        if i > 0:
            x = x + beta.sqrt() * torch.randn_like(x)
    return x


def train_smoke(cfg: DiffusionConfig) -> Dict:
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    if cfg.synthetic:
        data = make_synthetic_signals(cfg)
    else:
        raise ValueError("Fournir --synthetic ou implémenter un loader de dataset autorisé dans ce script.")

    ds = TensorDataset(data)
    dl = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True)
    model = SmallDenoiser(cfg.channels).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    sched = DiffusionSchedule(cfg, device)
    mse = nn.MSELoss()

    losses = []
    model.train()
    for epoch in range(cfg.epochs):
        epoch_loss = 0.0
        n = 0
        for (x0,) in dl:
            x0 = x0.to(device)
            t = torch.randint(0, cfg.timesteps, (x0.size(0),), device=device, dtype=torch.long)
            noise = torch.randn_like(x0)
            xt = sched.q_sample(x0, t, noise)
            pred = model(xt, t)
            loss = mse(pred, noise)
            opt.zero_grad()
            loss.backward()
            opt.step()
            epoch_loss += float(loss.item()) * x0.size(0)
            n += x0.size(0)
        losses.append(epoch_loss / max(1, n))
        print(f"epoch={epoch+1}/{cfg.epochs} loss={losses[-1]:.6f}")

    model.eval()
    samples = p_sample_loop(model, sched, (4, cfg.channels, cfg.seq_len), device).cpu().numpy()
    result = {
        "config": asdict(cfg),
        "train_losses": losses,
        "final_loss": losses[-1] if losses else None,
        "sample_shape": list(samples.shape),
        "sample_mean": float(samples.mean()),
        "sample_std": float(samples.std()),
        "notes": [
            "Smoke test synthétique uniquement - pas une preuve de performance médicale.",
            "Le modèle est un petit débruiteur 1D pédagogique, pas un SOTA.",
            "Pour RCS-70, conserver seed, versions, logs, config et sorties réelles.",
        ],
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--timesteps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--n-samples", type=int, default=512)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out", default="experiments/results/diffusion_poc.json")
    args = parser.parse_args()

    cfg = DiffusionConfig(
        seed=args.seed,
        seq_len=args.seq_len,
        n_samples=args.n_samples,
        batch_size=args.batch_size,
        epochs=args.epochs,
        timesteps=args.timesteps,
        device=args.device,
        synthetic=args.synthetic,
        out=args.out,
    )
    res = train_smoke(cfg)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
