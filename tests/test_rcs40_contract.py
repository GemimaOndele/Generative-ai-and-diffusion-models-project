"""RCS-40 — le contrat de données est versionné, complet et cohérent avec le dictionnaire."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = json.loads((ROOT / "data" / "contracts" / "ai4i_v1.json").read_text(encoding="utf-8"))


def test_contract_versioned_and_traceable():
    assert C["version"] and C["date"]
    assert len(C["source"]["sha256"]) == 64 and C["source"]["licence"] == "CC BY 4.0"
    assert "NON médical" in C["source"]["categorie"]


def test_every_field_typed_with_control():
    for f in C["champs"]:
        assert f["type"] in {"int", "float", "str"}
        assert f["obligatoire"] is True
        assert ("min" in f) or ("domaine" in f), f["source"]


def test_dictionary_lists_every_contract_field():
    doc = (ROOT / "docs" / "24_rcs40_dictionnaire_contrat_donnees.md").read_text(encoding="utf-8")
    for f in C["champs"]:
        assert f["source"] in doc and f["cible"] in doc


def _validate_and_normalize(row):
    # Contrôle exécutable de référence du contrat, indépendant de l'ingestion RCS-49.
    import math
    out = {}
    for field in C["champs"]:
        raw = row[field["source"]]
        kind = field["type"]
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError(field["source"])
        value = {"int": int, "float": float, "str": str}[kind](raw)
        if kind != "str" and not math.isfinite(value):
            raise ValueError(field["source"])
        if "domaine" in field and value not in field["domaine"]:
            raise ValueError(field["source"])
        if field.get("min") is not None and value < field["min"]:
            raise ValueError(field["source"])
        if field.get("max") is not None and value > field["max"]:
            raise ValueError(field["source"])
        if field["cible"] == "cle_source":
            value = str(value)
        elif field["cible"] == "equipement_id":
            value = "AI4I-" + value
            assert value in field["domaine_cible"]
        out[field["cible"]] = value
    if out["process_temp_k"] < out["air_temp_k"]:
        raise ValueError("temperature coherence")
    return out


def _row():
    return dict(zip([f["source"] for f in C["champs"]], ["1","L","300","310","1500","42","0","0"]))


def test_contract_normalizes_valid_source_row():
    result = _validate_and_normalize(_row())
    assert result["cle_source"] == "1"
    assert result["equipement_id"] == "AI4I-L"
    assert result["air_temp_k"] == 300.0
    assert result["label"] == 0


def test_contract_rejects_invalid_rows():
    for name, value in [("UDI","1.5"),("UDI","0"),("Type","X"),("Air temperature [K]","nan"),("Air temperature [K]","400"),("Process temperature [K]","299"),("Rotational speed [rpm]","-1"),("Torque [Nm]","201"),("Tool wear [min]","401"),("Machine failure","2"),("Type","")]:
        try:
            _validate_and_normalize({**_row(), name: value})
        except ValueError:
            continue
        raise AssertionError(f"Invalid value accepted: {name}={value}")
