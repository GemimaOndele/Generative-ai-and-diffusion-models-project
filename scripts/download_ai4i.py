"""Télécharge AI4I 2020 depuis UCI (CC BY 4.0) dans data/raw/ et vérifie l'empreinte SHA-256."""
from __future__ import annotations

import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
EXPECTED = "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"
DEST = Path(__file__).resolve().parents[1] / "data" / "raw" / "ai4i2020.csv"


def main() -> None:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL, timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    data = z.read("ai4i2020.csv")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED:
        sys.exit(f"Empreinte inattendue {digest} : fichier modifié à la source, vérifier avant usage.")
    DEST.write_bytes(data)
    print(f"OK {DEST} sha256={digest}")


if __name__ == "__main__":
    main()
