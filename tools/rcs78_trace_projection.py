"""Project benchmark metadata into RCS-89 events, without copying free text.

The context is a reviewed provenance document, not a source of measured results.
Missing fallback evidence blocks the export. No models are executed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).resolve().parents[1] / "data/contracts/trace_event_v1.json"


class ProjectionError(ValueError):
    """A fixed diagnostic code, never a source value or exception text."""


def load_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ProjectionError("duplicate_json_key")
            result[key] = value
        return result
    def reject_constant(_):
        raise ProjectionError("nonfinite_json_number")
    try:
        return json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
    except (ValueError, TypeError, RecursionError):
        raise ProjectionError("invalid_json") from None


def number(value, nullable=False):
    if value is None and nullable:
        return None
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ProjectionError("invalid_numeric_metadata")
    return value


def validate_context(context, source_hash):
    fields = {"source_sha256", "boundary", "model_registry", "fallback_by_trace"}
    if type(context) is not dict or set(context) != fields:
        raise ProjectionError("invalid_context_fields")
    if context["source_sha256"] != source_hash:
        raise ProjectionError("source_hash_mismatch")
    if context["boundary"] not in ("local_compute", "remote_api", "hybrid"):
        raise ProjectionError("invalid_boundary")
    registry = context["model_registry"]
    if type(registry) is not dict or not registry:
        raise ProjectionError("missing_model_registry")
    # Values are controlled aliases; upstream model strings are only lookup keys.
    import re
    for value in registry.values():
        if type(value) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,47}", value):
            raise ProjectionError("invalid_model_alias")
    if len(set(registry.values())) != len(registry):
        raise ProjectionError("duplicate_model_alias")
    fallback = context["fallback_by_trace"]
    if type(fallback) is not dict or any(type(v) is not bool for v in fallback.values()):
        raise ProjectionError("invalid_fallback_evidence")


def project_bytes(raw, context, emitted_at=None):
    """Return events only after the entire source validates (no partial export).

    timestamp_utc denotes projection emission, not historical inference time.
    Caller must review registry, boundary and per-trace fallback evidence.
    """
    digest = hashlib.sha256(raw).hexdigest()
    validate_context(context, digest)
    validator = Draft202012Validator(load_json(SCHEMA.read_text(encoding="utf-8")))
    timestamp = emitted_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    events, seen = [], set()
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError:
        raise ProjectionError("invalid_encoding") from None
    for line in lines:
        if not line.strip():
            continue
        rec = load_json(line)
        if type(rec) is not dict:
            raise ProjectionError("invalid_record")
        trace = rec.get("trace_id")
        if type(trace) is not str or not trace or len(trace) > 256:
            raise ProjectionError("invalid_trace_identity")
        if trace in seen:
            raise ProjectionError("duplicate_trace_identity")
        seen.add(trace)
        if trace not in context["fallback_by_trace"]:
            raise ProjectionError("missing_fallback_evidence")
        fallback = context["fallback_by_trace"][trace]
        if "fallback_triggered" in rec and (type(rec["fallback_triggered"]) is not bool
                or rec["fallback_triggered"] != fallback):
            raise ProjectionError("conflicting_fallback_evidence")
        status = rec.get("status")
        if status not in ("ok", "fallback", "error"):
            raise ProjectionError("invalid_execution_status")
        if status == "fallback" and not fallback:
            raise ProjectionError("conflicting_fallback_evidence")
        models = rec.get("models")
        if type(models) is not list or any(type(m) is not str for m in models):
            raise ProjectionError("invalid_model_metadata")
        if any(m not in context["model_registry"] for m in models):
            raise ProjectionError("unregistered_model")
        aliases = list(dict.fromkeys(context["model_registry"][m] for m in models))
        version = "+".join(aliases) if aliases else "none"
        # Hash identity with source provenance; do not export source trace IDs.
        identity = hashlib.sha256((digest + "\0" + trace).encode()).hexdigest()
        event = {
            "schema_version": "1.0.0", "timestamp_utc": timestamp,
            "trace_id": "trc_" + identity[:56], "run_id": "projection_" + digest,
            "component": "orchestrator_j2", "model_version": version,
            "status": status, "latency_ms": number(rec.get("latency_ms")),
            "cost_eur": number(rec.get("cost_eur"), nullable=True),
            # Per-run energy must not be attributed to individual traces.
            "energy_kwh": None, "energy_kwh_status": "ND",
            "boundary": context["boundary"], "fallback_triggered": fallback,
            "error_code": "source_execution_error" if status == "error" else None,
        }
        if not validator.is_valid(event):
            raise ProjectionError("event_contract_violation")
        events.append(event)
    if not events:
        raise ProjectionError("no_traces")
    if set(context["fallback_by_trace"]) != seen:
        raise ProjectionError("unexpected_fallback_evidence")
    return events


def export_file(source, context_path, output):
    source, context_path, output = map(Path, (source, context_path, output))
    if output.resolve() in (source.resolve(), context_path.resolve()):
        raise ProjectionError("output_overwrites_input")
    events = project_bytes(source.read_bytes(), load_json(context_path.read_text(encoding="utf-8")))
    # Stage and atomically replace only after complete validation.
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                         delete=False, suffix=".tmp") as stream:
            staged = Path(stream.name)
            for event in events:
                stream.write(json.dumps(event, allow_nan=False, ensure_ascii=True) + "\n")
        os.replace(staged, output)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    return {"decision": "PROJECTED_NOT_APPROVED", "count": len(events),
            "energy_status": "ND", "clinical_validation": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = export_file(args.input, args.context, args.output)
    except ProjectionError as exc:
        print(json.dumps({"decision": "BLOCKED", "reason": str(exc)}))
        return 2
    except (OSError, UnicodeError):
        print(json.dumps({"decision": "BLOCKED", "reason": "io_error"}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
