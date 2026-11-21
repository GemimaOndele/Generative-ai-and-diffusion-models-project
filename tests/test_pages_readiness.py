"""Tests de contrat de la vitrine statique GitHub Pages.
Tests structuraux seulement, sans navigateur/serveur exécutés ici.
"""
import pathlib
import re
import unittest
from xml.etree import ElementTree

ROOT=pathlib.Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"

class TestPagesReadiness(unittest.TestCase):
    def test_pages_assets_and_nojekyll(self):
        for rel in ("index.html","landing.css","landing.js",".nojekyll",
                    "assets/robocare-hero-animated.svg","assets/architecture.svg"):
            with self.subTest(path=rel):
                self.assertTrue((DOCS/rel).is_file(),rel)
        for svg in ("robocare-hero-animated.svg","architecture.svg"):
            ElementTree.parse(DOCS/"assets"/svg)

    def test_landing_has_all_milestones_and_safety(self):
        html=(DOCS/"index.html").read_text(encoding="utf-8")
        js=(DOCS/"landing.js").read_text(encoding="utf-8")
        css=(DOCS/"landing.css").read_text(encoding="utf-8")
        for phrase in ("TP04","TP05","Diffusion","Green AI","Gémima",
                       "Aminata","Omar","Elias","Ayoub"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase,html+js)
        for phrase in ("aucun diagnostic", "aucune action", "Prototype"):
            self.assertTrue(phrase.lower() in (html+js).lower())
        self.assertIn("prefers-reduced-motion",css)
        self.assertIn('role="tablist"',html)
        self.assertIn("aria-expanded",html)
        self.assertIn("aria-selected",js)

    def test_no_unsafe_active_content(self):
        html=(DOCS/"index.html").read_text(encoding="utf-8").lower()
        js=(DOCS/"landing.js").read_text(encoding="utf-8").lower()
        for banned in ("<iframe","<form", "localstorage", "sessionstorage",
                       "navigator.geolocation", "document.cookie", "fetch(",
                       "api_key", "patient_name"):
            self.assertNotIn(banned,html+js)
        self.assertNotIn("onclick=",html)
        self.assertIn('rel="noopener noreferrer"',html)

    def test_admin_configuration_truthfully_documented(self):
        source=(ROOT/".github/REPOSITORY_PROFILE.md").read_text(encoding="utf-8")
        pages=(DOCS/"README_PAGES.md").read_text(encoding="utf-8")
        self.assertIn("gh-pages",source)
        self.assertIn("gh-pages / (root)",pages)
        self.assertIn("sans attendre la pr #1",pages.lower())
        self.assertIn("Settings",source)

if __name__=="__main__":
    unittest.main()
