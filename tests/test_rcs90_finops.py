"""Tests fictifs du calculateur FinOps ; aucun montant réellement dépensé."""
import csv
import tempfile
from pathlib import Path
import unittest

from tools.rcs90_finops import summarize, COST_REQUIRED, WORKLOG_REQUIRED


def csv_data(root, filename, fields, rows):
    path = root / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fields))
        writer.writeheader()
        writer.writerows(rows)
    return path


def cost(entry_id, amount, status="actual", included="no", source="facture-fictive"):
    return dict(entry_id=entry_id, jira_ticket="RCS-90", category="api",
                cost_class="variable", status=status, amount_eur=amount,
                currency="EUR", included_in_api=included, source_ref=source, notes="fictif")


def labor(entry_id, hours, status="actual", rate="", source=""):
    return dict(entry_id=entry_id, jira_ticket="RCS-90", member="test",
                activity="test", status=status, hours=hours,
                hypothetical_hourly_rate_eur=rate, rate_source=source, notes="fictif")


class TestFinops(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_summary(self, costs=None, logs=None, **kw):
        a = csv_data(self.root, "cost.csv", COST_REQUIRED, costs or [])
        b = csv_data(self.root, "hours.csv", WORKLOG_REQUIRED, logs or [])
        return summarize(a, b, **kw)

    def test_empty_is_nd_not_zero(self):
        z = self.run_summary()
        self.assertIsNone(z["cash_actual_observed_eur"])
        self.assertIsNone(z["work_hours_actual_reported"])
        self.assertIsNone(z["cost_per_success_observed_cash_eur"])

    def test_real_and_forecast_separated(self):
        z = self.run_summary([cost("a", "12.75"), cost("b", "31", "estimated")])
        self.assertEqual(z["cash_actual_observed_eur"], "12.75")
        self.assertEqual(z["cash_estimated_entries_eur"], "31.00")

    def test_prevent_api_double_counting(self):
        z = self.run_summary([cost("a", "12.00"), cost("b", "12.00", included="yes")])
        self.assertEqual(z["cash_actual_observed_eur"], "12.00")
        self.assertEqual(z["coverage"]["included_in_api_excluded"], 1)

    def test_duplicate_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "dupliqué"):
            self.run_summary([cost("same", "1"), cost("same", "2")])

    def test_incomplete_csv_rejected(self):
        a = self.root / "cost.csv"
        a.write_text(",".join(sorted(COST_REQUIRED)) + "\nshort\n", encoding="utf-8")
        b = csv_data(self.root, "hours.csv", WORKLOG_REQUIRED, [])
        with self.assertRaisesRegex(ValueError, "incomplète"):
            summarize(a, b)

    def test_ticket_required_for_cost(self):
        x = cost("x", "1")
        x["jira_ticket"] = ""
        with self.assertRaisesRegex(ValueError, "ticket"):
            self.run_summary([x])

    def test_eur_only(self):
        x = cost("usd", "5")
        x["currency"] = "USD"
        with self.assertRaisesRegex(ValueError, "EUR"):
            self.run_summary([x])

    def test_no_negative_cost(self):
        with self.assertRaises(ValueError):
            self.run_summary([cost("negative", "-1")])

    def test_cost_per_success_requires_evidence(self):
        with self.assertRaisesRegex(ValueError, "success_source"):
            self.run_summary([cost("a", "10")], successes=2)
        z = self.run_summary([cost("a", "10.00")],
                             successes=3, success_source="preuve-test-fictive")
        self.assertEqual(z["cost_per_success_observed_cash_eur"], "3.33")

    def test_zero_success_is_nd(self):
        z = self.run_summary([cost("a", "10")], successes=0,
                             success_source="preuve-fictive")
        self.assertIsNone(z["cost_per_success_observed_cash_eur"])

    def test_worklog_and_hypothetical_labor_separated(self):
        z = self.run_summary([cost("a", "2")],
                             [labor("h1", "2.5", rate="20", source="hypothèse"),
                              labor("h2", "3", status="estimated")])
        self.assertEqual(z["cash_actual_observed_eur"], "2.00")
        self.assertEqual(z["work_hours_actual_reported"], "2.50")
        self.assertEqual(z["work_hours_estimated"], "3.00")
        self.assertEqual(z["labor_hypothetical_eur"], "50.00")


if __name__ == "__main__":
    unittest.main()
