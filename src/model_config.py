"""Configuration explicite des modèles A/B et de la politique TP04 (RCS-75).

Aucun modèle, prix, licence ou droit n'est présumé : en mode live, la
configuration doit être fournie explicitement (fichier JSON ou variables
d'environnement) et validée avant le premier appel. Les champs inconnus
restent vides et aucun coût n'est inventé.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "oui"}


def _as_float(value: Any) -> Optional[float]:
    if value in (None, "", "None", "ND"):
        return None
    return float(value)


@dataclass(frozen=True)
class ModelSpec:
    """Identité et conditions d'usage d'un modèle. Aucune valeur par défaut 'réelle'."""

    label: str
    model_name: str
    provider: str
    version: str
    family: str = ""
    license: str = ""
    usage_rights_verified: bool = False
    region: str = ""
    retention_policy: str = ""
    data_transfer_authorized: bool = False
    base_url: str = ""
    api_key_env: str = ""
    price_in_eur_per_1k_input: Optional[float] = None
    price_in_eur_per_1k_output: Optional[float] = None
    is_demo: bool = False

    def identity(self) -> Tuple[str, str, str]:
        return (
            self.provider.strip().lower(),
            self.model_name.strip().lower(),
            self.version.strip().lower(),
        )

    def public_dict(self) -> Dict[str, Any]:
        """Métadonnées sans secret : ni clé, ni URL d'authentification."""
        data = asdict(self)
        data.pop("api_key_env", None)
        data.pop("base_url", None)
        return data

    def validate(self, *, live: bool) -> None:
        missing = [
            field
            for field in ("model_name", "provider", "version")
            if not str(getattr(self, field) or "").strip()
        ]
        if missing:
            raise ValueError(f"Modèle {self.label}: champs requis manquants: {', '.join(missing)}")
        if not live:
            return

        missing = [
            field
            for field in ("license", "region", "retention_policy", "base_url", "api_key_env")
            if not str(getattr(self, field) or "").strip()
        ]
        if missing:
            raise ValueError(f"Modèle {self.label}: configuration live incomplète: {', '.join(missing)}")
        if not self.usage_rights_verified:
            raise ValueError(f"Modèle {self.label}: droits d'utilisation non vérifiés")
        if not self.data_transfer_authorized:
            raise ValueError(f"Modèle {self.label}: transfert de données non autorisé")
        for field in ("price_in_eur_per_1k_input", "price_in_eur_per_1k_output"):
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValueError(f"Modèle {self.label}: {field} ne peut pas être négatif")


@dataclass(frozen=True)
class BenchmarkPolicy:
    """Règles figées avant l'expérience (H2 falsifiable, arrêts, budget)."""

    timeout_a_s: float = 8.0
    timeout_b_s: float = 15.0
    max_calls_per_case: int = 2
    max_cost_eur_per_case: Optional[float] = None
    v2_pattern: str = "cascade"  # "cascade" ou "routing"
    allow_paid_calls: bool = False

    def validate(self, *, live: bool) -> None:
        if self.v2_pattern not in {"cascade", "routing"}:
            raise ValueError(f"v2_pattern invalide: {self.v2_pattern!r} (attendu: cascade ou routing)")
        if self.max_calls_per_case < 1:
            raise ValueError("max_calls_per_case doit être >= 1")
        if self.timeout_a_s <= 0 or self.timeout_b_s <= 0:
            raise ValueError("Les timeouts doivent être positifs")
        if self.max_cost_eur_per_case is not None and self.max_cost_eur_per_case < 0:
            raise ValueError("max_cost_eur_per_case ne peut pas être négatif")
        if live and not self.allow_paid_calls:
            raise ValueError("Appels payants interdits: allow_paid_calls doit être vrai en mode live")


def validate_pair(spec_a: ModelSpec, spec_b: ModelSpec, *, live: bool = False) -> None:
    """TP04 exige deux modèles réellement distincts, pas le même modèle derrière deux endpoints."""
    spec_a.validate(live=live)
    spec_b.validate(live=live)
    if spec_a.identity() == spec_b.identity():
        raise ValueError("A et B désignent le même modèle (fournisseur/nom/version identiques)")
    if (
        spec_a.model_name.strip().lower() == spec_b.model_name.strip().lower()
        and spec_a.version.strip().lower() == spec_b.version.strip().lower()
    ):
        raise ValueError("A et B désignent le même modèle sous deux fournisseurs différents")


class CostLedger:
    """Budget par cas. Un coût inconnu reste ND et bloque tout plafond configuré."""

    def __init__(self, max_cost_eur: Optional[float] = None):
        self.max_cost_eur = max_cost_eur
        self.spent_eur = 0.0
        self.cost_known = True
        self.calls = 0

    def estimate(self, spec: ModelSpec, input_tokens: Optional[int], output_tokens: Optional[int]) -> Optional[float]:
        if input_tokens is None or output_tokens is None:
            return None
        if spec.price_in_eur_per_1k_input is None or spec.price_in_eur_per_1k_output is None:
            return None
        return (input_tokens / 1000.0 * spec.price_in_eur_per_1k_input) + (
            output_tokens / 1000.0 * spec.price_in_eur_per_1k_output
        )

    def can_spend(self) -> Tuple[bool, Optional[str]]:
        if self.max_cost_eur is None:
            return True, None
        if not self.cost_known:
            return False, "cost_nd_with_cap"
        if self.spent_eur >= self.max_cost_eur:
            return False, "budget_exceeded"
        return True, None

    def record(self, spec: ModelSpec, input_tokens: Optional[int], output_tokens: Optional[int]) -> Tuple[Optional[float], Optional[str]]:
        self.calls += 1
        cost = self.estimate(spec, input_tokens, output_tokens)
        if cost is None:
            self.cost_known = False
            return None, "cost_nd"
        self.spent_eur += cost
        return cost, None


def load_config(path: str | Path) -> Tuple[ModelSpec, ModelSpec, BenchmarkPolicy]:
    """Charge un fichier JSON sans secret : {"models": {"A": {...}, "B": {...}}, "policy": {...}}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    models = data.get("models") or {}
    if not isinstance(models, dict) or "A" not in models or "B" not in models:
        raise ValueError("Le fichier de configuration doit contenir models.A et models.B")
    spec_a = ModelSpec(label="A", **models["A"])
    spec_b = ModelSpec(label="B", **models["B"])
    policy = BenchmarkPolicy(**(data.get("policy") or {}))
    validate_pair(spec_a, spec_b, live=True)
    policy.validate(live=True)
    return spec_a, spec_b, policy


def load_config_from_env() -> Tuple[ModelSpec, ModelSpec, BenchmarkPolicy]:
    """Configuration live minimale via variables d'environnement (jamais de clé dans le code)."""

    def spec(label: str) -> ModelSpec:
        prefix = f"LLM_{label}_"
        return ModelSpec(
            label=label,
            model_name=os.getenv(prefix + "MODEL", ""),
            provider=os.getenv(prefix + "PROVIDER", "openai-compatible"),
            version=os.getenv(prefix + "VERSION", os.getenv(prefix + "MODEL", "")),
            family=os.getenv(prefix + "FAMILY", ""),
            license=os.getenv(prefix + "LICENSE", ""),
            usage_rights_verified=_as_bool(os.getenv(prefix + "RIGHTS_VERIFIED")),
            region=os.getenv(prefix + "REGION", ""),
            retention_policy=os.getenv(prefix + "RETENTION", ""),
            data_transfer_authorized=_as_bool(os.getenv(prefix + "DATA_AUTHORIZED")),
            base_url=os.getenv(prefix + "BASE_URL", ""),
            api_key_env=f"LLM_{label}_API_KEY",
            price_in_eur_per_1k_input=_as_float(os.getenv(prefix + "PRICE_INPUT_EUR_PER_1K")),
            price_in_eur_per_1k_output=_as_float(os.getenv(prefix + "PRICE_OUTPUT_EUR_PER_1K")),
        )

    spec_a, spec_b = spec("A"), spec("B")
    policy = BenchmarkPolicy(
        timeout_a_s=float(os.getenv("TP04_TIMEOUT_A_S", "8")),
        timeout_b_s=float(os.getenv("TP04_TIMEOUT_B_S", "15")),
        max_calls_per_case=int(os.getenv("TP04_MAX_CALLS_PER_CASE", "2")),
        max_cost_eur_per_case=_as_float(os.getenv("TP04_MAX_COST_EUR_PER_CASE")),
        v2_pattern=os.getenv("TP04_V2_PATTERN", "cascade"),
        allow_paid_calls=_as_bool(os.getenv("TP04_ALLOW_PAID_CALLS")),
    )
    validate_pair(spec_a, spec_b, live=True)
    policy.validate(live=True)
    return spec_a, spec_b, policy
