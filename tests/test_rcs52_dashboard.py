"""RCS-52 — démo bout en bout + vue Streamlit. Ignoré si AI4I n'est pas téléchargé."""
import os
import subprocess
import sys
from pathlib import Path

import unittest
try:
    import pytest
except ModuleNotFoundError as exc:
    if exc.name != 'pytest':
        raise
    raise unittest.SkipTest('Suite RCS-52 exécutée par sa CI dédiée') from exc

ROOT = Path(__file__).resolve().parents[1]
AI4I = ROOT / "data" / "raw" / "ai4i2020.csv"
requires_ai4i = pytest.mark.skipif(not AI4I.exists(), reason="lancer scripts/download_ai4i.py")


@requires_ai4i
def test_demo_pipeline_then_dashboard(tmp_path, monkeypatch):
    db = tmp_path / "demo.sqlite"
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "demo_pipeline.py"), "--db", str(db),
                          "--limit", "300"], capture_output=True, text=True, encoding="utf-8", timeout=300,
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert out.returncode == 0, out.stderr
    assert "import 2 : deja_importe" in out.stdout

    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("RCS_DB", str(db))
    at = AppTest.from_file(str(ROOT / "src" / "rcs" / "ui" / "dashboard.py"), default_timeout=60).run()
    assert not at.exception
    assert any("Mesures et anomalies" in t.value for t in at.title)
    assert len(at.metric) == 4


def test_model_selection_prevents_duplicate_observations(tmp_path, monkeypatch):
    import csv
    sys.path.insert(0, str(ROOT / "src"))
    from contextlib import closing
    from rcs.db import connect
    from rcs.ingestion import CONTRACT, import_csv
    from rcs.alerts import enregistrer_analyse
    from streamlit.testing.v1 import AppTest
    path = tmp_path / "a.csv"
    row = dict(zip(CONTRACT, [1, "L", 300, 310, 1000, 40, 0, 1]))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CONTRACT)); writer.writeheader(); writer.writerow(row)
    db = tmp_path / "demo.sqlite"
    with closing(connect(db)) as conn:
        import_csv(conn, path)
        oid = conn.execute("SELECT id FROM observation").fetchone()[0]
        enregistrer_analyse(conn, oid, "a@v1", 5, 2)
        enregistrer_analyse(conn, oid, "b@v2", 7, 3)
    monkeypatch.setenv("RCS_DB", str(db))
    at = AppTest.from_file(str(ROOT / "src" / "rcs" / "ui" / "dashboard.py"), default_timeout=60).run()
    assert not at.exception
    at.sidebar.selectbox[0].select("AI4I-L").run()
    assert not at.exception
    assert at.metric[0].value == "1" and at.metric[3].value == "1"
    version = next(w for w in at.sidebar.selectbox if w.label == "Version du modèle")
    version.select("b@v2").run()
    assert not at.exception
    assert at.metric[0].value == "1" and at.metric[3].value == "1"
    frame = at.dataframe[0].value
    assert len(frame) == 1 and frame.iloc[0]["model_version"] == "b@v2" and frame.iloc[0]["score"] == 7
