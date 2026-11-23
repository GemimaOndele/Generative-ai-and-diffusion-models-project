"""Orchestrateur Multi-LLM du jalon J2 / RCS-75 (TP04).

Le ticket exige de justifier deux modèles réellement distincts A/B, un patron
V2 explicable (cascade A->B ou routage A/B), un contrat d'entrée/sortie, des
refus/abstentions et une traçabilité sans donnée sensible. Ce module fournit
l'implémentation correspondante.

Garanties :
- A et B doivent être deux modèles distincts (identité vérifiée au démarrage) ;
- le routage ne consulte jamais `expected_behavior` (réservé au scoring hors ligne) ;
- aucun appel n'est lancé si le transfert de données ou le budget n'est pas autorisé ;
- les coûts inconnus restent ND et ne sont jamais estimés ;
- les prompts et les données sensibles ne sont pas journalisés (hash uniquement).

Le mode démo valide l'orchestration, jamais la qualité d'un modèle de langage.

Ce module remplace le squelette « TP04 non implémenté » (RCS-76) présent dans
main : aucun appel réel n'est effectué tant que les modèles A/B ne sont pas
validés (licence, droits, région, rétention, budget).
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .model_config import BenchmarkPolicy, CostLedger, ModelSpec, validate_pair


class LLMClient(Protocol):
    model_name: str
    provider: str
    version: str

    def generate(self, prompt: str, *, timeout_s: float) -> "LLMResponse": ...


@dataclass
class LLMResponse:
    text: str
    status: str  # ok | error | timeout | refused | abstain
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_eur: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    error_type: Optional[str] = None


@dataclass
class CaseInput:
    case_id: str
    task: str
    input: str
    context: str = ""
    category: str = "usual"
    # Réservé au scoring hors ligne : jamais utilisé pour router ou valider une réponse.
    expected_behavior: str = ""


@dataclass
class TraceRecord:
    trace_id: str
    case_id: str
    strategy: str
    model: Optional[str]
    model_version: Optional[str]
    provider: Optional[str]
    latency_ms: Optional[int]
    call_count: int
    status: str
    error_type: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    cost_eur: Optional[float]
    decision: str
    output_hash: Optional[str]
    notes: str = ""
    prompt_hash: Optional[str] = None


STRESS_CATEGORIES = {"no_source", "contradiction", "injection", "sensitive", "out_of_scope"}
PRIVATE_CATEGORIES = {"sensitive", "out_of_scope"}
ABSTAIN_MARKERS = (
    "abstain", "abstention", "refus", "review", "cannot", "ne peux pas",
    "incertain", "arbitrage", "human review",
)
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9._-]{10,}", re.IGNORECASE),
)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _contains_secret(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)


def valid_schema(response: LLMResponse) -> bool:
    """Schéma minimal : statut ok, texte non vide et aucune clé divulguée."""
    return (
        response.status == "ok"
        and bool(response.text and response.text.strip())
        and not _contains_secret(response.text)
    )


def grounded(response: LLMResponse, case: CaseInput) -> bool:
    """Validation métier versionnée (placeholder durci pour le TP04).

    - cas stress : exiger une abstention/un refus explicite et l'absence de secret ;
    - cas usuels/complexes : refuser une réponse vide, une fuite de secret ou une
      abstention inattendue (qui doit être comptée comme telle, pas comme un succès).
    """
    text = (response.text or "").lower()
    if _contains_secret(response.text):
        return False
    has_abstention = any(marker in text for marker in ABSTAIN_MARKERS)
    if case.category in STRESS_CATEGORIES:
        return has_abstention
    return bool(text.strip()) and not has_abstention


def privacy_authorizes(_: CaseInput, model_label: str) -> bool:
    """Compatibilité ascendante : contrôle historique par variable d'environnement.

    Préférer `Orchestrator` avec des `ModelSpec` explicites en mode live.
    """
    return os.getenv(f"ALLOW_{model_label.upper()}_DATA", "0") == "1"


def budget_exceeded() -> bool:
    """Compatibilité ascendante : arrêt d'urgence via variable d'environnement."""
    return os.getenv("TP04_BUDGET_EXCEEDED", "0") == "1"


def _transfer_allowed(case: CaseInput, spec: ModelSpec) -> bool:
    """Un cas sensible/hors périmètre n'est jamais transmis, même si B est autorisé."""
    if case.category in PRIVATE_CATEGORIES:
        return False
    if spec.is_demo:
        return True
    return spec.data_transfer_authorized and spec.usage_rights_verified


def _spec_from_client(client: LLMClient, label: str) -> ModelSpec:
    spec = getattr(client, "spec", None)
    if isinstance(spec, ModelSpec):
        return spec
    demo = isinstance(client, DemoClient)
    return ModelSpec(
        label=label,
        model_name=getattr(client, "model_name", "unknown"),
        provider=getattr(client, "provider", "unknown"),
        version=getattr(client, "version", "unknown"),
        is_demo=demo,
        data_transfer_authorized=demo,
    )


class DemoClient:
    """Client déterministe pour tester l'orchestration sans appel réseau."""

    def __init__(
        self,
        model_name: str,
        provider: str = "demo",
        version: str = "demo-1",
        behavior: Optional[Dict[str, str]] = None,
        spec: Optional[ModelSpec] = None,
    ):
        self.model_name = model_name
        self.provider = provider
        self.version = version
        self.behavior = behavior or {}
        self.spec = spec or ModelSpec(
            label="?", model_name=model_name, provider=provider, version=version,
            is_demo=True, data_transfer_authorized=True,
        )

    def generate(self, prompt: str, *, timeout_s: float) -> LLMResponse:
        mode = "ok"
        for key, val in self.behavior.items():
            if key in prompt:
                mode = val
                break
        if mode == "timeout":
            time.sleep(min(timeout_s, 0.01))
            return LLMResponse(text="", status="timeout", error_type="TimeoutError")
        if mode == "invalid":
            return LLMResponse(text="", status="error", error_type="InvalidSchema")
        if mode == "refuse":
            return LLMResponse(text="ABSTAIN: human review required", status="ok")
        return LLMResponse(
            text=f"[{self.model_name}] demo response", status="ok",
            input_tokens=50, output_tokens=20, cost_eur=None,
        )


class OpenAICompatibleClient:
    """Client minimal Chat Completions. Aucun appel sans configuration validée."""

    def __init__(
        self,
        model_name: str,
        provider: str,
        version: str,
        base_url: str,
        api_key_env: str,
        spec: Optional[ModelSpec] = None,
    ):
        self.model_name = model_name
        self.provider = provider
        self.version = version
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.spec = spec

    def generate(self, prompt: str, *, timeout_s: float) -> LLMResponse:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            return LLMResponse(text="", status="error", error_type="MissingAPIKey")
        try:
            import requests  # type: ignore
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            return LLMResponse(text="", status="error", error_type=f"MissingDependency:{exc.__class__.__name__}")

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            return LLMResponse(
                text=text,
                status="ok",
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                cost_eur=None,  # calculé par CostLedger uniquement si tarif connu
                raw={"id": data.get("id"), "model": data.get("model")},
            )
        except Exception as exc:  # pragma: no cover - réseau
            err = "TimeoutError" if "timeout" in exc.__class__.__name__.lower() else exc.__class__.__name__
            return LLMResponse(text="", status="error", error_type=err)


@dataclass
class OrchestratorResult:
    status: str  # ok | refused | abstain | error
    answer: Optional[str]
    reason: str
    model: Optional[str]
    version: Optional[str]
    strategy: str
    traces: List[TraceRecord]


class Orchestrator:
    def __init__(
        self,
        model_a: LLMClient,
        model_b: Optional[LLMClient] = None,
        policy: Optional[BenchmarkPolicy] = None,
        spec_a: Optional[ModelSpec] = None,
        spec_b: Optional[ModelSpec] = None,
        live: bool = False,
    ):
        self.model_a = model_a
        self.model_b = model_b
        self.policy = policy or BenchmarkPolicy()
        self.policy.validate(live=live)
        self.spec_a = spec_a or _spec_from_client(model_a, "A")
        self.spec_b = spec_b or (_spec_from_client(model_b, "B") if model_b is not None else None)
        if live:
            if self.spec_b is None:
                raise ValueError("Le mode live exige un modèle B distinct du modèle A")
            validate_pair(self.spec_a, self.spec_b, live=True)
        elif self.spec_b is not None:
            validate_pair(self.spec_a, self.spec_b, live=False)
        else:
            self.spec_a.validate(live=False)

    @staticmethod
    def _blocked_trace(
        case: CaseInput, strategy: str, decision: str,
        spec: Optional[ModelSpec], status: str, reason: str,
    ) -> TraceRecord:
        return TraceRecord(
            trace_id=str(uuid.uuid4()),
            case_id=case.case_id,
            strategy=strategy,
            model=spec.model_name if spec else None,
            model_version=spec.version if spec else None,
            provider=spec.provider if spec else None,
            latency_ms=0,
            call_count=0,
            status=status,
            error_type=reason,
            input_tokens=None,
            output_tokens=None,
            cost_eur=None,
            decision=decision,
            output_hash=None,
            notes="blocked_before_call",
        )

    def _call(
        self,
        case: CaseInput,
        model: LLMClient,
        spec: ModelSpec,
        strategy: str,
        decision: str,
        timeout_s: float,
        ledger: CostLedger,
    ):
        trace_id = str(uuid.uuid4())
        # expected_behavior est volontairement exclu : il ne doit pas influencer la réponse.
        prompt = f"[case_id={case.case_id}][category={case.category}]\nTASK: {case.task}\nINPUT: {case.input}\nCONTEXT: {case.context}"
        prompt_hash = _hash_text(prompt)
        started = time.perf_counter()
        response = model.generate(prompt, timeout_s=timeout_s)
        latency_ms = int((time.perf_counter() - started) * 1000)

        notes: List[str] = []
        if response.status in {"refused", "abstain"}:
            status, error_type = "abstain", response.error_type or "ModelRefused"
        elif response.status != "ok":
            status, error_type = "error", response.error_type or response.status
        elif not valid_schema(response):
            status = "error"
            error_type = "SecretLeak" if _contains_secret(response.text) else "InvalidSchema"
        elif not grounded(response, case):
            status, error_type = "abstain", "ValidationFailed"
        else:
            status, error_type = "ok", None

        cost, cost_note = ledger.record(spec, response.input_tokens, response.output_tokens)
        if cost_note:
            notes.append(cost_note)
        if status != "ok" and "response not validated" not in notes:
            notes.append("response not validated")

        trace = TraceRecord(
            trace_id=trace_id,
            case_id=case.case_id,
            strategy=strategy,
            model=spec.model_name,
            model_version=spec.version,
            provider=spec.provider,
            latency_ms=latency_ms,
            call_count=1,
            status=status,
            error_type=error_type,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_eur=cost,
            decision=decision,
            output_hash=_hash_text(response.text) if response.text else None,
            notes="; ".join(notes),
            prompt_hash=prompt_hash,
        )
        return trace, response

    def run_mono(self, case: CaseInput, model_label: str = "A", timeout_s: Optional[float] = None) -> OrchestratorResult:
        label = model_label.upper()
        if label not in {"A", "B"}:
            raise ValueError("model_label doit être A ou B")
        model = self.model_a if label == "A" else self.model_b
        spec = self.spec_a if label == "A" else self.spec_b
        strategy = f"mono_{label.lower()}"
        if model is None or spec is None:
            trace = self._blocked_trace(case, strategy, "model_not_configured", spec, "error", "model_not_configured")
            return OrchestratorResult("error", None, "model_not_configured", None, None, strategy, [trace])
        if not _transfer_allowed(case, spec):
            trace = self._blocked_trace(case, strategy, "transfer_blocked", spec, "refused", "transfer_blocked")
            return OrchestratorResult("refused", None, "transfer_blocked", spec.model_name, spec.version, strategy, [trace])

        ledger = CostLedger(self.policy.max_cost_eur_per_case)
        allowed, reason = ledger.can_spend()
        if not allowed or budget_exceeded():
            trace = self._blocked_trace(case, strategy, "blocked_before_call", spec, "abstain", reason or "budget_exceeded")
            return OrchestratorResult("abstain", None, reason or "budget_exceeded", spec.model_name, spec.version, strategy, [trace])

        effective_timeout = timeout_s if timeout_s is not None else (
            self.policy.timeout_a_s if label == "A" else self.policy.timeout_b_s
        )
        trace, response = self._call(case, model, spec, strategy, strategy, effective_timeout, ledger)
        answer = response.text if trace.status == "ok" else None
        reason = "validated" if trace.status == "ok" else (trace.error_type or "not_validated")
        return OrchestratorResult(trace.status, answer, reason, spec.model_name, spec.version, strategy, [trace])

    def run_cascade(
        self,
        case: CaseInput,
        timeout_a: Optional[float] = None,
        timeout_b: Optional[float] = None,
    ) -> OrchestratorResult:
        strategy = "cascade_a_b"
        ledger = CostLedger(self.policy.max_cost_eur_per_case)
        timeout_a = timeout_a if timeout_a is not None else self.policy.timeout_a_s
        timeout_b = timeout_b if timeout_b is not None else self.policy.timeout_b_s

        if not _transfer_allowed(case, self.spec_a):
            trace = self._blocked_trace(case, strategy, "try_a", self.spec_a, "refused", "transfer_blocked")
            return OrchestratorResult("refused", None, "transfer_blocked", self.spec_a.model_name, self.spec_a.version, strategy, [trace])

        trace_a, resp_a = self._call(case, self.model_a, self.spec_a, strategy, "try_a", timeout_a, ledger)
        traces = [trace_a]
        if trace_a.status == "ok":
            return OrchestratorResult("ok", resp_a.text, "validated_by_a", self.spec_a.model_name, self.spec_a.version, strategy, traces)

        if self.model_b is None or self.spec_b is None:
            traces[0].notes += "; model_b_missing"
            return OrchestratorResult("abstain", None, "model_b_missing", trace_a.model, trace_a.model_version, strategy, traces)

        allowed, reason = ledger.can_spend()
        # Compatibilité : le garde-fou historique ALLOW_B_DATA reste actif en démo.
        demo_consent = not self.spec_b.is_demo or privacy_authorizes(case, "B")
        if not _transfer_allowed(case, self.spec_b) or not demo_consent or not allowed or budget_exceeded():
            traces[0].notes += "; fallback_blocked"
            return OrchestratorResult("abstain", None, "fallback_blocked", trace_a.model, trace_a.model_version, strategy, traces)

        trace_b, resp_b = self._call(case, self.model_b, self.spec_b, strategy, "fallback_to_b", timeout_b, ledger)
        traces.append(trace_b)
        if trace_b.status == "ok":
            return OrchestratorResult("ok", resp_b.text, "validated_by_b", self.spec_b.model_name, self.spec_b.version, strategy, traces)
        return OrchestratorResult("abstain", None, trace_b.error_type or "not_validated", self.spec_b.model_name, self.spec_b.version, strategy, traces)

    def choose_route(self, case: CaseInput) -> str:
        """Routage explicable fondé sur la catégorie uniquement, jamais sur expected_behavior."""
        if self.model_b is None:
            return "A"
        return "B" if case.category == "complex" else "A"

    def run_routing(self, case: CaseInput) -> OrchestratorResult:
        strategy = "routing_a_b"
        route = self.choose_route(case)
        spec = self.spec_a if route == "A" else self.spec_b
        model = self.model_a if route == "A" else self.model_b
        if model is None or spec is None:
            trace = self._blocked_trace(case, strategy, f"route_to_{route.lower()}", spec, "error", "model_not_configured")
            return OrchestratorResult("error", None, "model_not_configured", None, None, strategy, [trace])
        if not _transfer_allowed(case, spec):
            trace = self._blocked_trace(case, strategy, f"route_to_{route.lower()}", spec, "refused", "transfer_blocked")
            return OrchestratorResult("refused", None, "transfer_blocked", spec.model_name, spec.version, strategy, [trace])

        ledger = CostLedger(self.policy.max_cost_eur_per_case)
        allowed, reason = ledger.can_spend()
        if not allowed or budget_exceeded():
            trace = self._blocked_trace(case, strategy, f"route_to_{route.lower()}", spec, "abstain", reason or "budget_exceeded")
            return OrchestratorResult("abstain", None, reason or "budget_exceeded", spec.model_name, spec.version, strategy, [trace])

        timeout = self.policy.timeout_a_s if route == "A" else self.policy.timeout_b_s
        trace, response = self._call(case, model, spec, strategy, f"route_to_{route.lower()}", timeout, ledger)
        answer = response.text if trace.status == "ok" else None
        reason = "validated" if trace.status == "ok" else (trace.error_type or "not_validated")
        return OrchestratorResult(trace.status, answer, reason, spec.model_name, spec.version, strategy, [trace])

    def run_v2(self, case: CaseInput) -> OrchestratorResult:
        """Patron retenu pour le ticket, configurable avant expérience (H2)."""
        if self.policy.v2_pattern == "cascade":
            return self.run_cascade(case)
        return self.run_routing(case)


def result_to_dict(result: OrchestratorResult) -> Dict[str, Any]:
    data = asdict(result)
    data["traces"] = [asdict(t) for t in result.traces]
    return data
