"""RoboCare Sentinel — POC académique (ECE MSc2 IA) d'aide à la maintenance d'équipements.

Le paquet ne pilote, ne diagnostique et ne répare AUCUNE machine médicale réelle.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "experiments" / "results"
CORPUS = ROOT / "corpus"

__version__ = "0.1.0"
