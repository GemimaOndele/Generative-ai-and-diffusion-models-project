"""Contrôles unitaires d'une diffusion vraiment entraînée — synthétique seulement."""
import math
import unittest
import numpy as np

from experiments.rcs69_diffusion_numpy import (
    ALPHA_BAR, D, T, Denoiser, experiment, synthetic_signals, mad_scores
)


class TestLearnedSyntheticDiffusion(unittest.TestCase):
    def test_synthetic_is_reproducible(self):
        a=synthetic_signals(np.random.default_rng(7),20)
        b=synthetic_signals(np.random.default_rng(7),20)
        np.testing.assert_allclose(a,b)
        self.assertEqual(a.shape,(20,D))

    def test_real_train_updates_weights(self):
        train=synthetic_signals(np.random.default_rng(5),60)
        model=Denoiser(8)
        before=model.params["w1"].copy()
        losses=model.train(train,np.random.default_rng(9),updates=30)
        self.assertEqual(model.n_updates,30)
        self.assertEqual(len(losses),30)
        self.assertTrue(all(math.isfinite(v) for v in losses))
        self.assertFalse(np.array_equal(before,model.params["w1"]))

    def test_reverse_sampling_is_finite(self):
        model=Denoiser(3)
        model.train(synthetic_signals(np.random.default_rng(4),60),
                    np.random.default_rng(12),updates=25)
        samples=model.sample(np.random.default_rng(17),n=4)
        self.assertEqual(samples.shape,(4,D))
        self.assertTrue(np.isfinite(samples).all())

    def test_training_and_validation_split_and_metrics(self):
        result=experiment(seed=42,updates=80)
        self.assertEqual(result["scope"],"synthetic_signal_research_only_not_medical")
        self.assertEqual(result["train_normal"],320)
        self.assertEqual(result["test_anomaly"],64)
        self.assertEqual(result["generated_samples_count"],3)
        self.assertTrue(result["sample_finite"])
        for key in ("baseline_MAD","learned_diffusion_denoiser"):
            cm=result[key]
            self.assertEqual(cm["TP"]+cm["FN"],64)
            self.assertEqual(cm["FP"]+cm["TN"],64)

    def test_reproducible_test_metrics_same_seed(self):
        a=experiment(42,updates=60)
        b=experiment(42,updates=60)
        self.assertEqual(a["dataset_sha256"],b["dataset_sha256"])
        self.assertEqual(a["baseline_MAD"],b["baseline_MAD"])
        self.assertEqual(a["learned_diffusion_denoiser"],b["learned_diffusion_denoiser"])

    def test_reject_invalid_training(self):
        model=Denoiser(1)
        with self.assertRaises(ValueError):
            model.train(np.zeros((2,D)),np.random.default_rng(3),updates=5)
        with self.assertRaises(ValueError):
            experiment(updates=0)


if __name__=="__main__":
    unittest.main()
