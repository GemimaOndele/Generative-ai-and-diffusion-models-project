"""Tests du contrat de capacité : toutes les disponibilités de test sont fictives."""
import csv
import tempfile
from pathlib import Path
import unittest

from tools.rcs17_sprint0 import assess_capacity

MEMBERS = ("Gémima", "Aminata", "Omar", "Elias", "Ayoub")


class TestCapacity(unittest.TestCase):
    def make(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "capacity.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=("member", "available_hours", "approved", "evidence_ref"))
            w.writeheader()
            w.writerows(rows)
        return path

    def test_all_pending_is_blocked(self):
        p = self.make([{"member": m, "available_hours": "", "approved": "pending", "evidence_ref": ""} for m in MEMBERS])
        r = assess_capacity(p)
        self.assertFalse(r["ready_for_manual_planning"])
        self.assertIsNone(r["recorded_capacity_hours"])
        self.assertEqual(r["approved_count"], 0)

    def test_valid_approved_fixture_is_ready_to_plan_not_auto_start(self):
        rows = [{"member": m, "available_hours": "2.5", "approved": "yes", "evidence_ref": "confirmation-fictive"} for m in MEMBERS]
        r = assess_capacity(self.make(rows))
        self.assertTrue(r["ready_for_manual_planning"])
        self.assertFalse(r["ready_to_start_automatically"])
        self.assertEqual(r["recorded_capacity_hours"], "12.5")

    def test_no_approval_without_hours(self):
        rows = [{"member": m, "available_hours": "", "approved": "yes", "evidence_ref": "fictif"} for m in MEMBERS]
        with self.assertRaisesRegex(ValueError, "heures"):
            assess_capacity(self.make(rows))

    def test_duplicate_member_rejected(self):
        rows = [{"member": "Gémima", "available_hours": "", "approved": "pending", "evidence_ref": ""}]*2
        with self.assertRaisesRegex(ValueError, "dupliquée"):
            assess_capacity(self.make(rows))

    def test_negative_hours_rejected(self):
        rows = [{"member": "Gémima", "available_hours": "-1", "approved": "pending", "evidence_ref": ""}]
        with self.assertRaisesRegex(ValueError, "positive"):
            assess_capacity(self.make(rows))


if __name__ == "__main__":
    unittest.main()
