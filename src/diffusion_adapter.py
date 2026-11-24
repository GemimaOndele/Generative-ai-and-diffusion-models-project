"""Entraînement/adaptation diffusion J1 reproductible — RCS-57.

Le ticket demande des essais contrôlés, des seeds, des logs, des
hyperparamètres et deux variantes, avec pour critère d'acceptation une
exécution reproductible et des outputs conservés. Ce module fournit :

* un mini-DDPM 1D déterministe (q_sample / débruitage), sans dépendance
  externe, pour que la preuve soit rejouable en CI ;
* deux variantes contrôlées : ``base`` (débruiteur sans conditionnement
  temporel) et ``adapte`` (même données, même schedule, même optimiseur,
  seul le conditionnement temporel change) ;
* la journalisation des hyperparamètres, des seeds, des pertes par époque
  et des mesures calculées à partir de l'exécution réelle ;
* une preuve d'acceptation vérifiable par ``python -m src.diffusion_adapter
  --acceptance``.

Périmètre : J1 (détection/reconstruction de signaux), smoke test sur signaux
synthétiques. Aucune mesure clinique, aucun seuil de détection, aucun résultat
de modèle pré-entraîné, aucune date, version ou licence n'est revendiqué.
Les seuils restent ND et doivent être harmonisés puis gelés avant campagne
(RCS-22 / RCS-81). Le « V2 » du TP04 est une orchestration J2 et n'est pas une
optimisation de ce détecteur DDPM.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path

ND = "ND"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_PATH = PROJECT_ROOT / "experiments/results/rcs57_diffusion_variants.json"
DEFAULT_PROOF_PATH = PROJECT_ROOT / "governance/rcs57_acceptance.json"
VARIANTS = ("base", "adapte")

# Reprise littérale de la fiche Jira RCS-57 (champs structurés, aucune invention).
TICKET_METADATA = {
    "key": "RCS-57",
    "summary": "Entraîner ou adapter modèle de diffusion pour J1",
    "source": "bibliothèque RoboCare Sentinel V3",
    "phase": "S4",
    "objective": "Essais contrôlés, seeds, logs, hyperparamètres, deux variantes",
    "acceptance": "Exécution reproductible et outputs conservés",
    "competence": "Diffusion",
    "roles": {
        "responsable": "Elias",
        "binome": "Ayoub",
        "relais": "Omar",
        "relecteur": "Gémima",
    },
    "volets": [
        "contribution du pilote",
        "apprentissage accompagné du binôme",
        "recherche/veille documentée si la mission le requiert",
    ],
    "blockage": (
        "documenter obstacle, essais et liens dans ce ticket ; solliciter le "
        "binôme et le relais, puis arbitrer au point de coordination"
    ),
    "planification": "dates, estimations, Sprint et démarrage à fixer lors de la planification",
}


@dataclass(frozen=True)
class DiffusionConfig:
    """Hyperparamètres figés d'une campagne : toute modification change le run_id."""

    seed: int = 42
    n_train: int = 48
    n_test: int = 8
    seq_len: int = 16
    timesteps: int = 16
    batch_size: int = 16
    epochs: int = 2
    lr: float = 0.02
    hidden: int = 8
    time_dim: int = 8
    beta_start: float = 0.0001
    beta_end: float = 0.02
    variants: tuple[str, ...] = VARIANTS


DEFAULT_CONFIG = DiffusionConfig()

LIMITS = (
    "Signaux entièrement synthétiques : aucune preuve médicale ou industrielle.",
    "Mini-débruiteur pédagogique, pas un modèle SOTA ni un modèle pré-entraîné.",
    "Aucun seuil de détection n'est gelé ici : il reste ND avant campagne validée.",
    "La reconstruction mesurée ne vaut pas comparaison baseline vs diffusion (RCS-71).",
    "V2 (orchestration J2) n'est pas une optimisation directe de ce DDPM J1.",
    "Aucun GPU, réseau, version de modèle, licence, coût ou CO2e n'est revendiqué.",
)


def config_as_dict(config: DiffusionConfig = DEFAULT_CONFIG) -> dict:
    """Configuration au format JSON (les tuples deviennent des listes)."""
    return json.loads(json.dumps(asdict(config), ensure_ascii=False))


def config_fingerprint(config: DiffusionConfig = DEFAULT_CONFIG) -> str:
    return canonical_hash(config_as_dict(config))[:12]


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _randn(rng: random.Random) -> float:
    """Gaussienne Box-Muller déterministe (indépendante des versions numpy)."""
    u1 = rng.random()
    while u1 <= 0.0:
        u1 = rng.random()
    u2 = rng.random()
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def linear_schedule(config: DiffusionConfig) -> tuple[list[float], list[float]]:
    """Bêta linéaire et alpha_bar cumulé, identiques pour les deux variantes."""
    if config.timesteps < 2:
        raise ValueError("timesteps >= 2 requis")
    beta = [
        config.beta_start
        + (config.beta_end - config.beta_start) * i / (config.timesteps - 1)
        for i in range(config.timesteps)
    ]
    alpha_bar: list[float] = []
    cumulative = 1.0
    for value in beta:
        cumulative *= 1.0 - value
        alpha_bar.append(cumulative)
    return beta, alpha_bar


def make_signals(count: int, config: DiffusionConfig, seed: int) -> list[list[float]]:
    """Signaux synthétiques déterministes : sinusoïdes + bruit, normalisés."""
    rng = _rng(seed)
    signals = []
    for _ in range(count):
        amplitude = 0.6 + 0.8 * rng.random()
        frequency = 0.8 + 0.4 * rng.random()
        phase = 2.0 * math.pi * rng.random()
        values = []
        for index in range(config.seq_len):
            position = index / max(1, config.seq_len - 1)
            clean = amplitude * math.sin(4.0 * math.pi * frequency * position + phase)
            values.append(clean + 0.05 * _randn(rng))
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std = math.sqrt(variance) + 1e-6
        signals.append([(value - mean) / std for value in values])
    return signals


def time_embedding(timestep: int, config: DiffusionConfig) -> list[float]:
    """Encodage sinusoïdal du pas de diffusion (variante « adapte »)."""
    half = max(1, config.time_dim // 2)
    position = timestep / max(1, config.timesteps - 1)
    embedding: list[float] = []
    for index in range(half):
        inv_freq = 10000.0 ** (-(2 * index) / max(1, config.time_dim - 1))
        angle = position * inv_freq * math.pi
        embedding.extend((math.sin(angle), math.cos(angle)))
    return embedding[: config.time_dim]


@dataclass
class Denoiser:
    input_dim: int
    conditioned: bool
    W1: list[list[float]]
    b1: list[float]
    W2: list[list[float]]
    b2: list[float]


def init_denoiser(config: DiffusionConfig, conditioned: bool, seed: int) -> Denoiser:
    rng = _rng(seed)
    input_dim = config.seq_len + (config.time_dim if conditioned else 0)
    limit1 = math.sqrt(2.0 / input_dim)
    limit2 = math.sqrt(2.0 / config.hidden)
    return Denoiser(
        input_dim=input_dim,
        conditioned=conditioned,
        W1=[[_randn(rng) * limit1 for _ in range(input_dim)] for _ in range(config.hidden)],
        b1=[0.0] * config.hidden,
        W2=[[_randn(rng) * limit2 for _ in range(config.hidden)] for _ in range(config.seq_len)],
        b2=[0.0] * config.seq_len,
    )


def _forward(
    model: Denoiser, xt: list[float], timestep: int, config: DiffusionConfig
) -> tuple[list[float], list[float], list[float], list[float]]:
    inputs = list(xt)
    if model.conditioned:
        inputs = inputs + time_embedding(timestep, config)
    pre_hidden = [
        sum(weight * value for weight, value in zip(row, inputs)) + bias
        for row, bias in zip(model.W1, model.b1)
    ]
    hidden = [value if value > 0.0 else 0.0 for value in pre_hidden]
    output = [
        sum(weight * value for weight, value in zip(row, hidden)) + bias
        for row, bias in zip(model.W2, model.b2)
    ]
    return output, inputs, hidden, pre_hidden


def _zero_grads(model: Denoiser) -> dict:
    hidden = len(model.b1)
    return {
        "W1": [[0.0] * model.input_dim for _ in range(hidden)],
        "b1": [0.0] * hidden,
        "W2": [[0.0] * hidden for _ in model.b2],
        "b2": [0.0] * len(model.b2),
    }


def _accumulate(
    model: Denoiser,
    grads: dict,
    error: list[float],
    inputs: list[float],
    hidden: list[float],
    pre_hidden: list[float],
    config: DiffusionConfig,
) -> None:
    scale = 2.0 / config.seq_len
    for j in range(config.seq_len):
        delta = scale * error[j]
        grads["b2"][j] += delta
        for k, value in enumerate(hidden):
            grads["W2"][j][k] += delta * value
    for k in range(config.hidden):
        hidden_delta = 0.0
        for j in range(config.seq_len):
            hidden_delta += model.W2[j][k] * (scale * error[j])
        if pre_hidden[k] <= 0.0:  # ReLU
            hidden_delta = 0.0
        grads["b1"][k] += hidden_delta
        for index, value in enumerate(inputs):
            grads["W1"][k][index] += hidden_delta * value


def _apply(model: Denoiser, grads: dict, config: DiffusionConfig, count: int) -> None:
    step = config.lr / max(1, count)
    for j in range(config.seq_len):
        model.b2[j] -= step * grads["b2"][j]
        for k in range(config.hidden):
            model.W2[j][k] -= step * grads["W2"][j][k]
    for k in range(config.hidden):
        model.b1[k] -= step * grads["b1"][k]
        for index in range(model.input_dim):
            model.W1[k][index] -= step * grads["W1"][k][index]


def train_variant(
    config: DiffusionConfig,
    variant: str,
    train: list[list[float]],
    alpha_bar: list[float],
    seed: int,
) -> dict:
    """Entraîne un débruiteur epsilon-prédictif ; une seule variable change."""
    if variant not in VARIANTS:
        raise ValueError(f"variante inconnue: {variant}")
    conditioned = variant == "adapte"
    model = init_denoiser(config, conditioned, seed)
    rng = _rng(seed + 100)
    order = list(range(len(train)))
    epoch_losses: list[float] = []

    for _ in range(config.epochs):
        rng.shuffle(order)
        loss_sum = 0.0
        seen = 0
        for start in range(0, len(order), config.batch_size):
            batch = order[start : start + config.batch_size]
            grads = _zero_grads(model)
            for index in batch:
                x0 = train[index]
                timestep = rng.randrange(config.timesteps)
                sqrt_ab = math.sqrt(alpha_bar[timestep])
                sqrt_one_minus = math.sqrt(max(0.0, 1.0 - alpha_bar[timestep]))
                noise = [_randn(rng) for _ in range(config.seq_len)]
                xt = [sqrt_ab * x + sqrt_one_minus * n for x, n in zip(x0, noise)]
                predicted, inputs, hidden, pre_hidden = _forward(model, xt, timestep, config)
                error = [prediction - n for prediction, n in zip(predicted, noise)]
                loss_sum += sum(value * value for value in error) / config.seq_len
                seen += 1
                _accumulate(model, grads, error, inputs, hidden, pre_hidden, config)
            _apply(model, grads, config, len(batch))
        epoch_losses.append(loss_sum / max(1, seen))

    return {"model": model, "conditioned": conditioned, "seed": seed, "epoch_losses": epoch_losses}


def evaluate_variant(
    config: DiffusionConfig,
    model: Denoiser,
    test: list[list[float]],
    beta: list[float],
    alpha_bar: list[float],
    seed: int,
) -> dict:
    """Mesures calculées sur l'exécution : erreur de bruit et reconstruction DDPM."""
    rng = _rng(seed + 200)

    noise_sse = 0.0
    for x0 in test:
        timestep = rng.randrange(config.timesteps)
        sqrt_ab = math.sqrt(alpha_bar[timestep])
        sqrt_one_minus = math.sqrt(max(0.0, 1.0 - alpha_bar[timestep]))
        noise = [_randn(rng) for _ in range(config.seq_len)]
        xt = [sqrt_ab * x + sqrt_one_minus * n for x, n in zip(x0, noise)]
        predicted, _, _, _ = _forward(model, xt, timestep, config)
        noise_sse += sum((p - n) ** 2 for p, n in zip(predicted, noise)) / config.seq_len

    reconstruction_sse = 0.0
    for x0 in test:
        xt = [_randn(rng) for _ in range(config.seq_len)]
        for timestep in reversed(range(config.timesteps)):
            predicted, _, _, _ = _forward(model, xt, timestep, config)
            sqrt_alpha = math.sqrt(max(1e-12, 1.0 - beta[timestep]))
            coefficient = beta[timestep] / math.sqrt(max(1e-12, 1.0 - alpha_bar[timestep]))
            xt = [(value - coefficient * p) / sqrt_alpha for value, p in zip(xt, predicted)]
            if timestep > 0:
                noise = [_randn(rng) for _ in range(config.seq_len)]
                scale = math.sqrt(beta[timestep])
                xt = [value + scale * n for value, n in zip(xt, noise)]
        reconstruction_sse += sum((g - o) ** 2 for g, o in zip(xt, x0)) / config.seq_len

    return {
        "noise_prediction_mse": noise_sse / max(1, len(test)),
        "reconstruction_mse": reconstruction_sse / max(1, len(test)),
        "n_test": len(test),
    }


def run_experiment(config: DiffusionConfig = DEFAULT_CONFIG) -> dict:
    """Exécute les deux variantes avec les mêmes données et le même schedule."""
    beta, alpha_bar = linear_schedule(config)
    train = make_signals(config.n_train, config, config.seed)
    test = make_signals(config.n_test, config, config.seed + 1000)
    variants: dict[str, dict] = {}

    for variant in config.variants:
        # Même seed pour les deux variantes : seul le conditionnement change.
        trained = train_variant(config, variant, train, alpha_bar, config.seed)
        metrics = evaluate_variant(config, trained["model"], test, beta, alpha_bar, config.seed)
        variants[variant] = {
            "conditionnement_temporel": trained["conditioned"],
            "seed": trained["seed"],
            "epoch_losses": trained["epoch_losses"],
            "final_train_loss": trained["epoch_losses"][-1],
            "noise_prediction_mse": metrics["noise_prediction_mse"],
            "reconstruction_mse": metrics["reconstruction_mse"],
            "n_test": metrics["n_test"],
        }

    return {
        "ticket": "RCS-57",
        "jalon": "J1",
        "run_id": config_fingerprint(config),
        "config": config_as_dict(config),
        "data": {
            "generator": "sinusoïdes + bruit gaussien, déterministes",
            "n_train": config.n_train,
            "n_test": config.n_test,
            "seed_train": config.seed,
            "seed_test": config.seed + 1000,
            "seq_len": config.seq_len,
        },
        "schedule": "linear, identique pour les deux variantes",
        "variants": variants,
        "runtime": "Python stdlib (math, random, json) ; ni GPU, ni réseau, ni modèle pré-entraîné",
        "limits": list(LIMITS),
    }


def validate_ticket_metadata(metadata: dict = TICKET_METADATA) -> list[str]:
    errors = []
    for name in ("key", "summary", "source", "phase", "objective", "acceptance", "competence", "blockage", "planification"):
        if not metadata.get(name):
            errors.append(f"ticket.{name}: champ vide")
    for role, person in metadata.get("roles", {}).items():
        if not person:
            errors.append(f"ticket.roles.{role}: champ vide")
    if len(metadata.get("volets", ())) != 3:
        errors.append("ticket.volets: trois volets attendus")
    return errors


def validate_run(run: dict, config: DiffusionConfig = DEFAULT_CONFIG) -> list[str]:
    """Vérifie la structure et la cohérence interne de l'artefact conservé."""
    errors = []
    if not isinstance(run, dict):
        return ["run: objet JSON attendu"]
    if run.get("ticket") != "RCS-57" or run.get("jalon") != "J1":
        errors.append("run: identité RCS-57/J1 absente")
    if run.get("config") != config_as_dict(config):
        errors.append("run.config: hyperparamètres divergents")
    if run.get("run_id") != config_fingerprint(config):
        errors.append("run.run_id: empreinte de configuration incohérente")
    data = run.get("data", {})
    if not isinstance(data, dict):
        return errors + ["run.data: objet attendu"]
    if data.get("n_train") != config.n_train or data.get("n_test") != config.n_test:
        errors.append("run.data: effectifs divergents")
    if data.get("seed_train") != config.seed or data.get("seed_test") != config.seed + 1000:
        errors.append("run.data: seeds divergents")

    variants = run.get("variants", {})
    if not isinstance(variants, dict):
        return errors + ["run.variants: objet attendu"]
    if list(variants) != list(config.variants):
        errors.append("run.variants: deux variantes attendues (base, adapte)")
    for name in config.variants:
        variant = variants.get(name, {})
        if not isinstance(variant, dict):
            errors.append(f"{name}: objet attendu")
            continue
        if variant.get("conditionnement_temporel") is not (name == "adapte"):
            errors.append(f"{name}: conditionnement temporel incohérent")
        if variant.get("seed") != config.seed:
            errors.append(f"{name}: seed non déterministe")
        losses = variant.get("epoch_losses", [])
        if not isinstance(losses, list):
            errors.append(f"{name}.epoch_losses: liste attendue")
            continue
        if len(losses) != config.epochs:
            errors.append(f"{name}.epoch_losses: {config.epochs} époques attendues")
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0 for value in losses):
            errors.append(f"{name}.epoch_losses: valeurs invalides")
        if variant.get("final_train_loss") != (losses[-1] if losses else None):
            errors.append(f"{name}.final_train_loss: incohérent avec les logs")
        for metric in ("noise_prediction_mse", "reconstruction_mse"):
            value = variant.get(metric)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                errors.append(f"{name}.{metric}: mesure invalide")
        if variant.get("n_test") != config.n_test:
            errors.append(f"{name}.n_test: effectif divergent")
    raw_limits = run.get("limits", [])
    if not isinstance(raw_limits, list) or not all(isinstance(item, str) for item in raw_limits):
        return errors + ["run.limits: liste de textes attendue"]
    limits = " ".join(raw_limits)
    for token in ("synthétiques", "ND", "pas une optimisation"):
        if token not in limits:
            errors.append(f"run.limits: mention « {token} » absente")
    return errors


def _close(left: float, right: float) -> bool:
    return abs(left - right) <= 1e-9 + 1e-6 * abs(right)


def _read_run(run_path: str | Path) -> tuple[dict | None, list[str]]:
    path = Path(run_path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return None, ["artifact: objet JSON attendu"]
        return value, []
    except (OSError, ValueError) as exc:
        return None, [f"artifact.lecture: {exc}"]


def _display_path(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def acceptance_check(
    run_path: str | Path = DEFAULT_RUN_PATH, config: DiffusionConfig = DEFAULT_CONFIG
) -> dict:
    """Preuve d'acceptation : rejoue l'expérience et compare aux outputs conservés."""
    metadata_errors = validate_ticket_metadata()
    run, read_errors = _read_run(run_path)
    run_errors = validate_run(run, config) if run is not None else ["artifact: absent"]

    reproducibility_errors: list[str] = []
    if run is not None and not run_errors:
        replay = run_experiment(config)
        for name in config.variants:
            saved = run["variants"][name]
            fresh = replay["variants"][name]
            if len(saved["epoch_losses"]) != len(fresh["epoch_losses"]) or any(
                not _close(left, right)
                for left, right in zip(saved["epoch_losses"], fresh["epoch_losses"])
            ):
                reproducibility_errors.append(f"{name}.epoch_losses: rejeu divergent")
            for metric in ("noise_prediction_mse", "reconstruction_mse"):
                if not _close(saved[metric], fresh[metric]):
                    reproducibility_errors.append(f"{name}.{metric}: rejeu divergent")

    criteria = [
        {"id": "TICKET_FIELDS", "ok": not metadata_errors, "evidence": metadata_errors or TICKET_METADATA},
        {
            "id": "TWO_CONTROLLED_VARIANTS",
            "ok": run is not None and list(run.get("variants", {})) == list(config.variants),
            "evidence": "base (sans conditionnement) vs adapte (conditionné) ; données/schedule/lr/époques identiques",
        },
        {
            "id": "FIXED_SEEDS",
            "ok": run is not None and not any("seed" in error for error in run_errors),
            "evidence": f"seed={config.seed} identique pour les deux variantes, test={config.seed + 1000}",
        },
        {
            "id": "HYPERPARAMETERS_LOGGED",
            "ok": run is not None and not any("config" in error or "run_id" in error for error in run_errors),
            "evidence": config_as_dict(config),
        },
        {
            "id": "LOGS_PRESERVED",
            "ok": run is not None and not any("epoch_losses" in error for error in run_errors),
            "evidence": "epoch_losses et final_train_loss conservés dans l'artefact JSON",
        },
        {
            "id": "OUTPUTS_PRESERVED",
            "ok": run is not None and not read_errors,
            "evidence": read_errors or _display_path(run_path),
        },
        {
            "id": "REPRODUCIBLE_EXECUTION",
            "ok": run is not None and not read_errors and not run_errors and not reproducibility_errors,
            "evidence": read_errors or run_errors or reproducibility_errors or "rejeu déterministe du même run_id, tolérance 1e-6",
        },
        {
            "id": "NO_INVENTED_RESULTS",
            "ok": run is not None and not reproducibility_errors and not any("mesure" in error for error in run_errors),
            "evidence": "toutes les mesures sont recalculées depuis le code ; aucune valeur figée revendiquée",
        },
        {
            "id": "SCOPE_J1_SYNTHETIC",
            "ok": run is not None and not any("limits" in error for error in run_errors),
            "evidence": "smoke test synthétique ; seuils ND ; pas de validation médicale ; V2 J2 hors périmètre",
        },
    ]

    return {
        "ok": not (metadata_errors or read_errors or run_errors or reproducibility_errors) and all(criterion["ok"] for criterion in criteria),
        "ticket": "RCS-57",
        "criteria": criteria,
        "artifact_sha256": canonical_hash(run) if run is not None else ND,
        "config_fingerprint": config_fingerprint(config),
        "errors": metadata_errors + read_errors + run_errors + reproducibility_errors,
        "scope": "preuve de reproductibilité logicielle, non validation scientifique",
    }


def write_run(config: DiffusionConfig = DEFAULT_CONFIG, out_path: str | Path = DEFAULT_RUN_PATH) -> dict:
    run = run_experiment(config)
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RCS-57 : diffusion J1 reproductible, deux variantes")
    parser.add_argument("--out", default=str(DEFAULT_RUN_PATH), help="artefact JSON des outputs")
    parser.add_argument("--acceptance", action="store_true", help="rejoue et vérifie la preuve d'acceptation")
    parser.add_argument("--proof-out", default=str(DEFAULT_PROOF_PATH), help="preuve JSON générée en mode --acceptance")
    args = parser.parse_args(argv)

    if args.acceptance:
        proof = acceptance_check(args.out)
        proof_path = Path(args.proof_out)
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(proof, ensure_ascii=False, indent=2))
        return 0 if proof["ok"] else 1

    run = write_run(DEFAULT_CONFIG, args.out)
    print(f"run_id={run['run_id']} variantes={','.join(run['variants'])} out={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
