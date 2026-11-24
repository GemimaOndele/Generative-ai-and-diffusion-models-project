"""RCS-49 — ingestion : acceptation/rejet, quarantaine, deux imports identiques sans doublon."""
import csv
import sys
from pathlib import Path

import unittest
try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != 'pytest':
        raise
    raise unittest.SkipTest('Suite RCS-49 exécutée par sa CI dédiée') from exc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rcs.db import connect  # noqa: E402
from rcs.ingestion import CONTRACT, import_csv  # noqa: E402

HEADER = list(CONTRACT) + ["Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]

def _row(udi, typ="M", air=298.1, proc=308.6, rpm=1551, torque=42.8, wear=0, fail=0):
    return {"UDI": udi, "Type": typ, "Air temperature [K]": air, "Process temperature [K]": proc,
            "Rotational speed [rpm]": rpm, "Torque [Nm]": torque, "Tool wear [min]": wear,
            "Machine failure": fail, "Product ID": f"P{udi}", "TWF": 0, "HDF": 0, "PWF": 0, "OSF": 0, "RNF": 0}


def _write(path: Path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return path


@pytest.fixture
def conn():
    c = connect(":memory:")
    c.execute("INSERT INTO utilisateur VALUES ('tech-01','T','technicien'),('obs-01','O','admin')")
    try:
        yield c
    finally:
        c.close()


def test_import_accepts_rejects_and_dedups(conn, tmp_path):
    rows = [_row(1), _row(2), _row(2),               # doublon
            _row(3, typ="X"),                         # type invalide
            _row(4, proc=290.0),                      # process < air
            _row(5, rpm="abc")]                       # type non numérique
    rep = import_csv(conn, _write(tmp_path / "a.csv", rows), quarantine_dir=tmp_path / "q")
    assert rep.statut == "importe"
    assert (rep.nb_acceptees, rep.nb_rejetees, rep.nb_doublons) == (2, 3, 1)
    assert list((tmp_path / "q").glob("*_rejets.jsonl"))


def test_same_file_twice_is_idempotent(conn, tmp_path):
    p = _write(tmp_path / "a.csv", [_row(1), _row(2)])
    assert import_csv(conn, p).statut == "importe"
    rep2 = import_csv(conn, p)
    assert rep2.statut == "deja_importe"
    assert conn.execute("SELECT COUNT(*) FROM lot_import").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM observation").fetchone()[0] == 2


def test_overlapping_file_does_not_duplicate_observations(conn, tmp_path):
    import_csv(conn, _write(tmp_path / "a.csv", [_row(1), _row(2)]))
    rep = import_csv(conn, _write(tmp_path / "b.csv", [_row(2), _row(3)]))
    assert rep.nb_acceptees == 1 and rep.nb_doublons == 1


def test_missing_columns_rejected(conn, tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("UDI,Type\n1,M\n", encoding="utf-8")
    assert import_csv(conn, p).statut == "rejete"


def test_default_quarantine_and_nonfinite_values(conn, tmp_path, monkeypatch):
    import json
    monkeypatch.setenv("RCS_QUARANTINE_DIR", str(tmp_path / "default-q"))
    p = _write(tmp_path / "invalid.csv", [_row(1), _row(2, rpm="nan"), _row(3, torque="inf")])
    rep = import_csv(conn, p)
    assert (rep.nb_acceptees, rep.nb_rejetees) == (1, 2)
    files = list((tmp_path / "default-q").glob("*_rejets.jsonl"))
    assert len(files) == 1
    assert len([json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]) == 2


def test_quarantine_write_failure_does_not_commit_lot(conn, tmp_path):
    p = _write(tmp_path / "invalid.csv", [_row(1, typ="X")])
    bad = tmp_path / "not-dir"
    bad.write_text("x")
    with pytest.raises(OSError):
        import_csv(conn, p, quarantine_dir=bad)
    assert conn.execute("SELECT COUNT(*) FROM lot_import").fetchone()[0] == 0


def test_default_quarantine_without_argument_or_environment(conn, tmp_path, monkeypatch):
    import json
    monkeypatch.delenv("RCS_QUARANTINE_DIR", raising=False)
    home = tmp_path / "home"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    source = _write(tmp_path / "reject.csv", [_row(1), _row(2, typ="X")])
    report = import_csv(conn, source)
    target = home / ".local" / "share" / "robocare_sentinel" / "quarantine" / f"reject_{report.sha256[:8]}_rejets.jsonl"
    rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    assert report.nb_rejetees == 1
    assert len(rows) == 1 and rows[0]["ligne"] == 3
    assert rows[0]["brut"]["Type"] == "X"
    assert conn.execute("SELECT nb_rejetees FROM lot_import").fetchone()[0] == 1
    assert import_csv(conn, source).statut == "deja_importe"
    assert len(target.read_text(encoding="utf-8").splitlines()) == 1


def test_contract_limits_match_ingestion():
    import json
    contract = json.loads((Path(__file__).resolve().parents[1] / "data/contracts/ai4i_v1.json").read_text(encoding="utf-8"))
    fields = {field["source"]: field for field in contract["champs"]}
    assert set(fields) == set(CONTRACT)
    for source, (_, dtype, lower, upper) in CONTRACT.items():
        field = fields[source]
        assert field["type"] == dtype.__name__
        if "domaine" not in field:
            assert field.get("min") == lower and field.get("max") == upper
    assert fields["Type"]["domaine"] == ["L", "M", "H"]
