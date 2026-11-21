"""RCS-49 — ingestion : acceptation/rejet, quarantaine, deux imports identiques sans doublon."""
import csv
import sys
from pathlib import Path

import pytest

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
    return c


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
