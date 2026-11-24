"""Tests RCS-55 : baseline règles/ML reproductible et sans fuite de calibration.

Les tests de structure (artefact, notebook) n'importent que la bibliothèque standard.
Les tests d'exécution sont ignorés si numpy/pandas/sklearn sont absents ou si
l'import du module échoue dans l'environnement courant.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "baseline_rules_ml.py"
NOTEBOOK_PATH = ROOT / "experiments" / "baseline_rules_ml.ipynb"
ARTIFACT_PATH = ROOT / "experiments" / "results" / "rcs55_baseline_rules_ml.json"

DEPENDANCES = ("numpy", "pandas", "sklearn")
MANQUANTES = tuple(name for name in DEPENDANCES if importlib.util.find_spec(name) is None)


class ArtefactEtNotebookTests(unittest.TestCase):
    def test_artefact_structure(self):
        self.assertTrue(ARTIFACT_PATH.exists(), f"Artefact absent : {ARTIFACT_PATH}")
        artefact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        for cle in ("schema", "status", "config", "protocol", "thresholds", "notes"):
            self.assertIn(cle, artefact)
        self.assertIn(artefact["status"], ("computed", "ND"))

        config = artefact["config"]
        for cle in ("seed", "test_size", "contamination", "z_threshold", "synthetic"):
            self.assertIn(cle, config)
        self.assertEqual(config["seed"], 42)

        protocole = artefact["protocol"]
        for cle in ("split", "seed", "test_size", "rule_calibration", "metrics"):
            self.assertIn(cle, protocole)
        self.assertIn("precision", protocole["metrics"])
        self.assertIn("recall", protocole["metrics"])
        self.assertIn("f1", protocole["metrics"])
        self.assertIn("confusion_matrix", protocole["metrics"])

        seuils = artefact["thresholds"]
        for cle in ("z_threshold", "isolation_forest_contamination", "decision_threshold"):
            self.assertIn(cle, seuils)
        self.assertIn("ND", str(seuils["decision_threshold"]))
        self.assertFalse(seuils["z_threshold"]["frozen"])
        self.assertFalse(seuils["isolation_forest_contamination"]["frozen"])

        if artefact["status"] == "computed":
            self.assertEqual(artefact["source"], "synthetic_smoke_test" if config["synthetic"] else "dataset")
            for cle in ("dataset", "rules_calibration", "rules_baseline", "isolation_forest_baseline"):
                self.assertIn(cle, artefact)
            self.assertEqual(artefact["rules_calibration"]["fitted_on"], "train_only")
            for cle in ("rules_baseline", "isolation_forest_baseline"):
                for metrique in ("precision", "recall", "f1"):
                    valeur = artefact[cle][metrique]
                    self.assertGreaterEqual(valeur, 0.0)
                    self.assertLessEqual(valeur, 1.0)
        else:
            self.assertIn("reason", artefact)
            for cle in ("rules_baseline", "isolation_forest_baseline"):
                self.assertNotIn(cle, artefact)

    def test_notebook_json_et_protocol(self):
        self.assertTrue(NOTEBOOK_PATH.exists(), f"Notebook absent : {NOTEBOOK_PATH}")
        nb = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(nb["nbformat"], 4)
        self.assertGreaterEqual(nb["nbformat_minor"], 4)
        types = [cellule["cell_type"] for cellule in nb["cells"]]
        self.assertIn("markdown", types)
        self.assertIn("code", types)
        source = "\n".join(
            ligne for cellule in nb["cells"] for ligne in cellule["source"]
        )
        for fonction in ("stratified_split", "fit_rule_calibration", "rule_based_predict", "run"):
            self.assertIn(fonction, source)
        for mot in ("RCS-55", "ND", "precision", "recall", "F1", "seed=42"):
            self.assertIn(mot, source)


@unittest.skipIf(bool(MANQUANTES), f"Dépendances absentes : {', '.join(MANQUANTES) or 'aucune'}")
class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            spec = importlib.util.spec_from_file_location("rcs55_baseline_rules_ml", MODULE_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:
            raise unittest.SkipTest(f"Import du module indisponible : {exc}") from exc
        cls.mod = module

    def test_determinisme_meme_seed(self):
        cfg = self.mod.RunConfig(synthetic=True, seed=42, n_samples=400)
        premier = json.dumps(self.mod.run(cfg), sort_keys=True, ensure_ascii=False)
        second = json.dumps(self.mod.run(cfg), sort_keys=True, ensure_ascii=False)
        self.assertEqual(premier, second)

    def test_split_stratifie_reproductible(self):
        cfg = self.mod.RunConfig(synthetic=True, seed=42, n_samples=400)
        df = self.mod.make_synthetic(cfg)
        X = df.drop(columns=["label"])
        y = df["label"].astype(int).to_numpy()
        premier = self.mod.stratified_split(X, y, cfg)
        second = self.mod.stratified_split(X, y, cfg)
        for a, b in zip(premier, second):
            if hasattr(a, "columns"):
                self.mod.pd.testing.assert_frame_equal(a, b)
            else:
                self.mod.np.testing.assert_array_equal(a, b)
        _, _, y_train, y_test = premier
        self.assertEqual(set(y_test), {0, 1})
        self.assertAlmostEqual(float(y_train.mean()), float(y_test.mean()), delta=0.02)

    def test_absence_fuite_calibration(self):
        mod = self.mod
        train = mod.pd.DataFrame({
            "f1": [0.0, 1.0, -1.0, 0.5, -0.5, 0.2, -0.2, 0.1],
            "f2": [0.0, -0.5, 0.5, 0.1, -0.1, 1.0, -1.0, 0.2],
        })
        test = mod.pd.DataFrame({
            "f1": [10.0, 10.5, 9.5, 10.2],
            "f2": [0.0, 0.1, -0.1, 0.05],
        })
        calibration = mod.fit_rule_calibration(train)
        mod.np.testing.assert_allclose(calibration.means, train.mean().to_numpy())
        mod.np.testing.assert_allclose(calibration.stds, train.std(ddof=0).to_numpy())
        self.assertEqual(calibration.as_dict()["fitted_on"], "train_only")

        prediction = mod.rule_based_predict(test, calibration, 3.0)
        attendu = (
            mod.np.abs((test.to_numpy() - train.mean().to_numpy()) / train.std(ddof=0).to_numpy()).max(axis=1) > 3.0
        ).astype(int)
        mod.np.testing.assert_array_equal(prediction, attendu)

        # Une calibration incluant le test modifierait les statistiques et la décision.
        cal_fuite = mod.fit_rule_calibration(mod.pd.concat([train, test], ignore_index=True))
        self.assertFalse(mod.np.allclose(cal_fuite.means, calibration.means))
        prediction_fuite = mod.rule_based_predict(test, cal_fuite, 3.0)
        self.assertFalse(mod.np.array_equal(prediction, prediction_fuite))

    def test_metriques_dans_intervalle(self):
        cfg = self.mod.RunConfig(synthetic=True, seed=42, n_samples=400)
        resultats = self.mod.run(cfg)
        self.assertEqual(resultats["status"], "computed")
        for cle in ("rules_baseline", "isolation_forest_baseline"):
            for metrique in ("precision", "recall", "f1"):
                valeur = resultats[cle][metrique]
                self.assertGreaterEqual(valeur, 0.0)
                self.assertLessEqual(valeur, 1.0)
            self.assertEqual(resultats[cle]["confusion_matrix_labels"], ["normal", "anomaly"])
            self.assertEqual(
                sum(sum(ligne) for ligne in resultats[cle]["confusion_matrix"]),
                resultats["dataset"]["test_rows"],
            )
            self.assertIsInstance(resultats[cle]["report"], str)


if __name__ == "__main__":
    unittest.main()
