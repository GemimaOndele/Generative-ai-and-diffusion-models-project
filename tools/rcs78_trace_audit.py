"""RCS-78: audit de couverture des traces J2; pas d'exécution LLM.

Ne copie jamais prompts, réponses, données personnelles ni clefs API dans le
rapport. Les statistiques des traces existantes sont indicatives, pas une revue
clinique et pas un jugement humain de réussite.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

ALLOWED_STRATEGIES = {"b0_extractive", "mono_a", "mono_b", "routing", "cascade"}
ALLOWED_VARIANTS = {"default", "noguards", "route8w", "tok60", "unspecified"}
ALLOWED_STATUSES = {"ok", "error", "fallback", "abstain", "refused", "timeout"}
ALLOWED_CASE_IDS = {f"T{i:02d}" for i in range(1, 11)}
REQUIRED = ("case_id", "strategy", "trace_id", "status", "latency_ms")
SENSITIVE_MARKERS = ("patient_name", "patient_id", "nir", "api_key", "token_secret", "raw_prompt")


def _nonnegative(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        n = Decimal(str(value))
    except InvalidOperation:
        return None
    return n if n.is_finite() and n >= 0 else None


def audit_traces(path: str | Path) -> dict:
    """Validate metadata coverage only; never include source answers in output."""
    records = []
    warnings = []
    with Path(path).open(encoding="utf-8") as stream:
        for lineno, raw in enumerate(stream, 1):
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid JSONL line {lineno}") from exc
            if not isinstance(rec, dict):
                raise ValueError(f"JSONL line {lineno} must be an object")
            missing = [key for key in REQUIRED if key not in rec]
            if missing:
                raise ValueError(f"Line {lineno}: missing metadata {', '.join(missing)}")
            identity = rec["trace_id"]
            if not isinstance(identity, str) or not identity.strip():
                raise ValueError("Invalid trace identity")
            records.append(rec)
    if not records:
        return {"decision": "BLOCKED", "reason": "no_traces", "count": 0,
                "summary": {}, "warnings": ["No source traces supplied."]}
    grouped = {}
    duplicates = 0
    invalid_latency = 0
    missing_cost = 0
    sensitive_field_count = 0
    observed = set()
    for rec in records:
        strategy = rec["strategy"]
        case = rec["case_id"]
        variant = rec.get("variant", "unspecified")
        status = rec["status"]
        if not isinstance(strategy, str) or strategy not in ALLOWED_STRATEGIES or not isinstance(variant, str) or variant not in ALLOWED_VARIANTS or not isinstance(case, str) or case not in ALLOWED_CASE_IDS or not isinstance(status, str) or status not in ALLOWED_STATUSES:
            raise ValueError("Unexpected metadata value; audit blocked without exporting source values")
        key = (strategy, variant)
        if any(marker in str(field).casefold() for field in rec for marker in SENSITIVE_MARKERS):
            sensitive_field_count += 1
        ident = (strategy, variant, case)
        if ident in observed:
            duplicates += 1
        observed.add(ident)
        latency = _nonnegative(rec["latency_ms"])
        if latency is None:
            invalid_latency += 1
        if _nonnegative(rec.get("cost_eur")) is None:
            missing_cost += 1
        bucket = grouped.setdefault(key, {"rows": 0, "case_ids": set(), "status": Counter(),
                                          "latencies": [], "score_coverage": 0,
                                          "model_evidence": 0})
        bucket["rows"] += 1
        if isinstance(case, str):
            bucket["case_ids"].add(case)
        bucket["status"][status] += 1
        if latency is not None:
            bucket["latencies"].append(latency)
        if rec.get("score") in (0, 1) and not isinstance(rec.get("score"), bool):
            bucket["score_coverage"] += 1
        if isinstance(rec.get("models"), list) and rec["models"]:
            bucket["model_evidence"] += 1

    public = {}
    for (strategy, variant), bucket in sorted(grouped.items()):
        lat = sorted(bucket["latencies"])
        p95_index = (95 * len(lat) + 99) // 100 - 1
        public[f"{strategy}:{variant}"] = {
            "rows": bucket["rows"],
            "unique_cases": len(bucket["case_ids"]),
            "case_coverage": sorted(bucket["case_ids"]),
            "execution_statuses": dict(sorted(bucket["status"].items())),
            "latency_observed": len(lat),
            "p95_latency_ms": str(lat[p95_index]) if lat else None,
            "proxy_score_coverage": bucket["score_coverage"],
            "model_trace_coverage": bucket["model_evidence"],
        }
    if duplicates:
        warnings.append("Duplicate strategy/variant/case records")
    if invalid_latency:
        warnings.append("Invalid or missing latency values")
    if missing_cost:
        warnings.append("Cost values ND: do not calculate cost per success")
    if sensitive_field_count:
        warnings.append("Potential sensitive field names: manual inspection required; no raw contents exported")
    warnings.append("Proxy scores are not human-reviewed business success")
    warnings.append("Energy from remote models must remain ND without measured provenance")
    return {
        "decision": "TRACE_METADATA_AUDITED_NOT_APPROVED",
        "count": len(records),
        "summary": public,
        "quality_checks": {"duplicate_case_strategy_variant": duplicates,
                           "invalid_latency_count": invalid_latency,
                           "missing_or_invalid_cost_count": missing_cost,
                           "potential_sensitive_field_rows": sensitive_field_count},
        "warnings": sorted(set(warnings)),
        "human_review_required": True,
        "clinical_validation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RCS-78: metadata-only trace audit")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_traces(args.input)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
