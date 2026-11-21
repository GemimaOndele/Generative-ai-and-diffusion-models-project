"""RCS-52 — démo bout en bout + vue Streamlit. Ignoré si AI4I n'est pas téléchargé."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AI4I = ROOT / "data" / "raw" / "ai4i2020.csv"
pytestmark = pytest.mark.skipif(not AI4I.exists(), reason="lancer scripts/download_ai4i.py")


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
