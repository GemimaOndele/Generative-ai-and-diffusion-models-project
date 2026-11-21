"""Tests de validateur TP04/TP05, tous les résultats numériques sont des fixtures fictives."""
import csv
import tempfile
from pathlib import Path
import unittest

from tools.rcs81_evaluate import summarize, CASE_COLUMNS, RUN_COLUMNS

IDS=[f"T{i:02d}" for i in range(1,11)]
CATS=["usual"]*4+["complex"]*2+[
    "stress_source_absente","stress_source_contradictoire",
    "stress_injection_indirecte","stress_donnee_sensible"
]

class TestJointEvaluation(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def write(self,name,columns,rows):
        p=self.root/name
        with p.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=sorted(columns));w.writeheader();w.writerows(rows)
        return p

    def cases(self,frozen=True):
        rows=[dict(case_id=i,category=c,expected_behavior="abstention ou réponse sourcée",
                  approval_state="frozen" if frozen else "pending",
                  freeze_commit="commit-demo-test" if frozen else "")
              for i,c in zip(IDS,CATS)]
        return self.write("cases.csv",CASE_COLUMNS,rows)

    def runs(self,missing=False,mock=False,empty_cost=False):
        rows=[]
        for strategy in ("mono-A","mono-B","V2"):
            for i in IDS:
                rows.append(dict(
                    case_id=i,strategy=strategy,model_id="LLM-A" if strategy=="mono-A" else "LLM-B" if strategy=="mono-B" else "LLM-A",
                    model_version="version-test",execution_mode="mock" if mock else "live",
                    success="pass" if i!="T08" else "fail",review_evidence="revue-fictive",
                    latency_ms="100",cost_eur="" if empty_cost else "0.01",
                    citation_status="verified",route_reason="règle de test" if strategy=="V2" else "",
                ))
        if missing: rows.pop()
        return self.write("runs.csv",RUN_COLUMNS,rows)

    def test_unfrozen_is_blocked(self):
        x=summarize(self.cases(False),self.runs())
        self.assertEqual(x["decision"],"BLOCKED")
        self.assertIsNone(x["results"])

    def test_empty_runs_is_blocked(self):
        r=self.write("empty.csv",RUN_COLUMNS,[])
        self.assertEqual(summarize(self.cases(),r)["reason"],"no_executed_results")

    def test_fictitious_complete_data_calculates_but_never_approves(self):
        x=summarize(self.cases(),self.runs())
        self.assertEqual(x["decision"],"COMPARISON_CALCULATED_NOT_APPROVED")
        self.assertEqual(x["go_no_go"],"REVUE HUMAINE REQUISE")
        self.assertEqual(x["results"]["mono-A"]["business_success_count"],9)
        self.assertEqual(x["results"]["mono-B"]["p95_latency_ms"],"100.000")
        self.assertEqual(x["results"]["V2"]["cost_per_success_eur"],"0.011111")
        self.assertIsNone(x["results"]["V2"]["remote_co2e_kg"])

    def test_mock_rejected(self):
        with self.assertRaisesRegex(ValueError,"mock"):
            summarize(self.cases(),self.runs(mock=True))

    def test_incomplete_strategies_rejected(self):
        with self.assertRaisesRegex(ValueError,"10 lignes"):
            summarize(self.cases(),self.runs(missing=True))

    def test_unknown_cost_remains_nd(self):
        x=summarize(self.cases(),self.runs(empty_cost=True))
        self.assertIsNone(x["results"]["mono-A"]["cost_total_eur"])
        self.assertIsNone(x["results"]["V2"]["cost_per_success_eur"])

if __name__=="__main__":
    unittest.main()
