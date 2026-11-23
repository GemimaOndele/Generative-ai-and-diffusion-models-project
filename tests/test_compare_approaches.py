"""Tests du module de comparaison RCS-22."""

import unittest

from src.compare_approaches import (
    APPROACHES,
    HYPOTHESES,
    PROTOCOL,
    provisional_choice,
    render_comparison_table,
    validate_no_results,
)


class CompareApproachesTest(unittest.TestCase):
    def test_three_approaches_plus_v2(self):
        self.assertEqual([approach.id for approach in APPROACHES], ["A", "B", "C", "V2"])
        self.assertEqual(len(HYPOTHESES), 4)

    def test_hypotheses_are_falsifiable(self):
        for hypothesis in HYPOTHESES:
            self.assertTrue(hypothesis.statement)
            self.assertTrue(hypothesis.falsifier)

    def test_protocol_stays_nd(self):
        self.assertTrue(PROTOCOL)
        self.assertTrue(all(axis.status == "ND" for axis in PROTOCOL))
        self.assertEqual(validate_no_results(), [])

    def test_provisional_choice_is_not_a_go(self):
        choice = provisional_choice()
        self.assertEqual(choice["reference"], "B. règles / ML")
        self.assertIn("provisoire", choice["status"])

    def test_rendered_table_contains_approaches(self):
        table = render_comparison_table()
        for approach in APPROACHES:
            self.assertIn(approach.id, table)
            self.assertIn(approach.name, table)


if __name__ == "__main__":
    unittest.main()
