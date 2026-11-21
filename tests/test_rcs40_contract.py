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
