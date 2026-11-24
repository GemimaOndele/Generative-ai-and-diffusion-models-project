"""Baseline mono-LLM reproductible (RCS-61).

La mission Jira demande des exécutions reproductibles sur les mêmes questions,
avec réponses, logs, évaluation et latence sur un workload défini. Ce module
fournit exactement cela avec un client déterministe : aucun appel réseau, aucun
résultat de qualité inventé, aucun coût estimé.

Ce que la preuve couvre :
- une seule stratégie `mono_a`, un seul appel par cas recevable ;
- une exécution déterministe (mêmes questions -> mêmes décisions et mêmes hashes) ;
- des traces sans prompt en clair ni donnée sensible, et un score automatique
  limité à la décision observable (voir `src/scoring.py`) ;
- une latence locale mesurée par l'orchestrateur, jamais une latence LLM réelle.

Ce que la preuve ne couvre pas : qualité du modèle, tarifs, latence réseau,
CO₂e, ni validation des cas avant une expérience live.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .model_config import BenchmarkPolicy
from .orchestrator import (
    CaseInput,
    DemoClient,
    LLMResponse,
    Orchestrator,
    OrchestratorResult,
    result_to_dict,
)
from .scoring import auto_score_case, summarize

DEFAULT_WORKLOAD = Path(__file__).resolve().parents[1] / "experiments" / "rcs61_workload.jsonl"

_ABSTAIN_TEXT = "ABSTAIN: human review required"
_STABLE_RESULT_FIELDS = (
    "status", "reason", "strategy", "model", "version", "calls",
    "decisions", "output_hashes",
)


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class BaselineMonoClient(DemoClient):
    """Client déterministe du baseline : pas de réseau, pas de hasard.

    Les cas `abstain_case_ids` produisent une abstention explicite ; les autres
    produisent une réponse démo stable. Les cas sensibles sont refusés par
    l'orchestrateur avant tout appel.
    """

    def __init__(self, abstain_case_ids: Optional[Iterable[str]] = None):
        super().__init__("demo-mono-a", provider="demo", version="v1")
        self.abstain_case_ids = set(abstain_case_ids or ())

    def generate(self, prompt: str, *, timeout_s: float) -> LLMResponse:
        for case_id in sorted(self.abstain_case_ids):
            if f"case_id={case_id}" in prompt:
                return LLMResponse(
                    text=_ABSTAIN_TEXT,
                    status="abstain",
                    input_tokens=50,
                    output_tokens=20,
                    error_type="ModelAbstained",
                )
        return super().generate(prompt, timeout_s=timeout_s)


def load_workload(path: str | Path = DEFAULT_WORKLOAD) -> List[CaseInput]:
    """Charge le workload défini du ticket (JSONL, une question par ligne)."""
    cases: List[CaseInput] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                cases.append(CaseInput(**json.loads(line)))
    if not cases:
        raise ValueError(f"Workload vide : {path}")
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("Les case_id du workload doivent être uniques")
    return cases


def _stable_payload(case: CaseInput, result: OrchestratorResult) -> Dict[str, Any]:
    """Champs reproductibles : ni trace_id aléatoire, ni latence mesurée."""
    return {
        "case": {
            "case_id": case.case_id,
            "category": case.category,
            "task": case.task,
            "content_hash": _hash_text(f"{case.input}\n{case.context}"),
        },
        "result": {
            "status": result.status,
            "reason": result.reason,
            "strategy": result.strategy,
            "model": result.model,
            "version": result.version,
            "calls": sum(trace.call_count for trace in result.traces),
            "decisions": [trace.decision for trace in result.traces],
            "output_hashes": [trace.output_hash for trace in result.traces],
        },
    }


def _digest(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def run_baseline(
    cases: Sequence[CaseInput],
    client: Optional[BaselineMonoClient] = None,
    *,
    model_label: str = "A",
) -> Dict[str, Any]:
    """Exécute le mono-LLM sur le workload et retourne lignes + résumé + digest."""
    orch = Orchestrator(
        client or BaselineMonoClient(abstain_case_ids={"M04"}),
        policy=BenchmarkPolicy(max_calls_per_case=1),
    )
    rows: List[Dict[str, Any]] = []
    payloads: List[Dict[str, Any]] = []
    for case in cases:
        result = orch.run_mono(case, model_label)
        row = result_to_dict(result)
        row.update(auto_score_case(case.category, result.status, result.reason))
        row["case_id"] = case.case_id
        row["case_category"] = case.category
        row["evidence"] = "demo_logic_only"
        stable = _stable_payload(case, result)
        row["reproducibility_digest"] = _digest(stable)
        payloads.append(stable)
        rows.append(row)
    return {
        "rows": rows,
        "summary": summarize(rows),
        "reproducibility_digest": _digest({"cases": payloads}),
    }


def verify_reproducibility(
    cases: Sequence[CaseInput], *, model_label: str = "A"
) -> bool:
    """Deux exécutions indépendantes doivent donner le même digest."""
    first = run_baseline(cases, model_label=model_label)
    second = run_baseline(cases, model_label=model_label)
    return first["reproducibility_digest"] == second["reproducibility_digest"]


def write_outputs(bundle: Dict[str, Any], out_prefix: str | Path, *, reproducible: bool) -> None:
    """Écrit logs JSONL/CSV et résumé JSON, sans résultat inventé."""
    out = Path(out_prefix)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = bundle["rows"]

    jsonl_path = out.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    csv_path = out.with_suffix(".csv")
    fieldnames = [
        "case_id", "case_category", "strategy", "status", "reason", "model", "version",
        "call_count", "latency_ms", "input_tokens", "output_tokens", "cost_eur",
        "auto_score", "note", "reproducibility_digest",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            trace = row["traces"][0] if row.get("traces") else {}
            writer.writerow({
                "case_id": row.get("case_id"),
                "case_category": row.get("case_category"),
                "strategy": row.get("strategy"),
                "status": row.get("status"),
                "reason": row.get("reason"),
                "model": row.get("model"),
                "version": row.get("version"),
                "call_count": trace.get("call_count", 0),
                "latency_ms": trace.get("latency_ms"),
                "input_tokens": trace.get("input_tokens"),
                "output_tokens": trace.get("output_tokens"),
                "cost_eur": trace.get("cost_eur"),
                "auto_score": row.get("auto_score"),
                "note": row.get("note"),
                "reproducibility_digest": row.get("reproducibility_digest"),
            })

    summary_path = out.with_name(out.name + "_summary.json")
    summary = {
        "summary": bundle["summary"],
        "reproducibility": {
            "digest": bundle["reproducibility_digest"],
            "verified": reproducible,
            "stable_fields": list(_STABLE_RESULT_FIELDS),
            "excluded_fields": ["trace_id", "latency_ms", "prompt"],
        },
        "evidence": {
            "mode": "demo_deterministic_client",
            "quality": "ND",
            "real_llm_latency": "ND",
            "cost": "ND",
            "co2e": "ND",
            "note": "Validation logicielle uniquement, pas une preuve de qualité LLM.",
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
