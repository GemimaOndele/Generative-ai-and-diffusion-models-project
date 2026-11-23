"""Tests de validation du contrat de traces JSON et de rejet PII (RCS-89)."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data" / "contracts" / "trace_event_v1.json"
DOC_PATH = ROOT / "docs" / "41_rcs89_monitoring_traces_seuils.md"


def _load_schema() -> dict:
    assert SCHEMA_PATH.exists(), f"Schéma manquant : {SCHEMA_PATH}"
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate_against_schema(payload: dict, schema: dict) -> list[str]:
    """Validateur léger autonome aligné sur les règles de trace_event_v1.json."""
    errors: list[str] = []
    props = schema["properties"]

    if schema.get("additionalProperties") is False:
        extra = set(payload.keys()) - set(props.keys())
        if extra:
            errors.append(f"Champs non autorisés : {sorted(extra)}")

    for req in schema.get("required", []):
        if req not in payload:
            errors.append(f"Champ requis manquant : {req}")

    for key, value in payload.items():
        if key not in props:
            continue
        spec = props[key]
        if "const" in spec and value != spec["const"]:
            errors.append(f"{key} doit valoir {spec['const']!r}")
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{key} valeur invalide : {value!r}")
        if "pattern" in spec and (not isinstance(value, str) or not re.fullmatch(spec["pattern"], value)):
            errors.append(f"{key} ne respecte pas le motif {spec['pattern']}")
        if "minimum" in spec and isinstance(value, (int, float)) and not isinstance(value, bool):
            if value < spec["minimum"]:
                errors.append(f"{key} doit être >= {spec['minimum']}")
    return errors


def _valid_sample() -> dict:
    return {
        "schema_version": "1.0.0",
        "timestamp_utc": "2026-11-23T11:30:00Z",
        "trace_id": "trc_20261123_0001",
        "run_id": "run_j2_local_01",
        "component": "orchestrator_j2",
        "model_version": "qwen2.5-7b-local-v1",
        "status": "ok",
        "latency_ms": 412.5,
        "cost_eur": 0.0,
        "energy_kwh": 0.00012,
        "energy_kwh_status": "estimated",
        "boundary": "local_compute",
        "fallback_triggered": False,
        "error_code": None,
    }


def test_schema_structure_and_strictness():
    schema = _load_schema()
    assert schema["additionalProperties"] is False
    for field in [
        "trace_id",
        "run_id",
        "model_version",
        "latency_ms",
        "cost_eur",
        "energy_kwh_status",
    ]:
        assert field in schema["required"], f"Champ requis absent du schéma : {field}"
    assert schema["properties"]["energy_kwh_status"]["enum"] == ["measured", "estimated", "ND"]


def test_valid_trace_event_passes():
    schema = _load_schema()
    errors = _validate_against_schema(_valid_sample(), schema)
    assert errors == [], f"Événement valide rejeté : {errors}"


def test_patient_pii_fields_are_rejected():
    schema = _load_schema()
    pii_samples = [
        {"patient_name": "Jean Dupont"},
        {"ipp": "IPP-987654"},
        {"ssn": "1 85 05 75 123 456"},
        {"dob": "1985-05-12"},
        {"clinical_note": "Perfuseur chambre 204"},
    ]
    for pii in pii_samples:
        payload = {**_valid_sample(), **pii}
        errors = _validate_against_schema(payload, schema)
        assert errors, f"Le payload PII {pii} aurait dû être rejeté"


def test_invalid_energy_status_rejected():
    schema = _load_schema()
    payload = {**_valid_sample(), "energy_kwh_status": "guessed"}
    errors = _validate_against_schema(payload, schema)
    assert errors, "Un energy_kwh_status hors [measured, estimated, ND] doit être rejeté"


def test_doc_mentions_thresholds_and_no_pii_rules():
    assert DOC_PATH.exists(), f"Documentation manquante : {DOC_PATH}"
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for token in [
        "trace_id",
        "run_id",
        "model_version",
        "latency_ms",
        "cost_eur",
        "energy_kwh_status",
        "latence p95",
        "taux d'erreur",
        "taux de fallback",
        "codecarbon",
        "additionalproperties: false",
    ]:
        assert token in text, f"Élément attendu absent de la doc : {token}"
