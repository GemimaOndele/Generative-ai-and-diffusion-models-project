"""Verify the single-source GitHub Pages publishing contract.

The real HTML/CSS/JS website lives on the gh-pages branch at / (root).
The main branch retains only README visual assets and publishing guidance.
These tests deliberately do NOT require a duplicate website under docs/.
"""
from pathlib import Path
import unittest
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class TestPagesReadiness(unittest.TestCase):
    def test_single_source_no_duplicated_website_on_main(self):
        for rel in ("index.html", "landing.css", "landing.js"):
            with self.subTest(path=rel):
                self.assertFalse((DOCS / rel).exists(),
                                 "Le site vitrine doit rester sur gh-pages uniquement")

    def test_readme_visuals_are_available_and_safe(self):
        for name in ("robocare-hero-animated.svg", "architecture.svg"):
            with self.subTest(name=name):
                path = DOCS / "assets" / name
                self.assertTrue(path.is_file())
                ElementTree.parse(path)
                xml = path.read_text(encoding="utf-8").lower()
                for forbidden in ("<script", "<foreignobject", "javascript:",
                                  "onload=", "onerror="):
                    self.assertNotIn(forbidden, xml)

    def test_admin_contract_is_documented(self):
        source = (ROOT / ".github/REPOSITORY_PROFILE.md").read_text(encoding="utf-8")
        pages = (DOCS / "README_PAGES.md").read_text(encoding="utf-8")
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertIn("gh-pages", source)
        self.assertIn("gh-pages / (root)", pages)
        self.assertIn("Settings", source)
        self.assertIn("Squash", contributing)
        self.assertIn("main /docs", pages)
        self.assertIn("publication", pages.lower())


if __name__ == "__main__":
    unittest.main()
