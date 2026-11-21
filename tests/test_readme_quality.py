"""Contrôle README et visuels GitHub. Ne teste pas l'IA ou la clinique."""
from pathlib import Path
from xml.etree import ElementTree as ET
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestReadmeQuality(unittest.TestCase):
    def test_readme_covers_all_lessons(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for label in ("C3", "TP04", "TP05", "CodeCarbon", "Green AI", "Gémima",
                      "Aminata", "Omar", "Elias", "Ayoub", "RCS-17", "RCS-90"):
            with self.subTest(label=label):
                self.assertIn(label, readme)
        self.assertIn("PR #1", readme)
        self.assertNotIn("../../pull/", readme, "Utiliser des URLs GitHub stables pour les PR")
        self.assertIn("non", readme.lower())

    def test_all_local_visual_assets_exist_and_are_safe(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for rel in ("docs/assets/robocare-hero-animated.svg", "docs/assets/architecture.svg"):
            with self.subTest(asset=rel):
                self.assertIn(rel, readme)
                data = (ROOT / rel).read_text(encoding="utf-8")
                ET.fromstring(data)
                for prohibited in ("<script", "<foreignObject", "javascript:", "onload=", "http://www.w3.org/1999/xlink"):
                    self.assertNotIn(prohibited, data)
        self.assertIn("<animate", (ROOT / "docs/assets/robocare-hero-animated.svg").read_text(encoding="utf-8"))

    def test_audit_is_linked(self):
        self.assertTrue((ROOT / "docs/GITHUB_AUDIT_2026-11-21.md").exists())
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/GITHUB_AUDIT_2026-11-21.md", text)

if __name__ == "__main__":
    unittest.main()
