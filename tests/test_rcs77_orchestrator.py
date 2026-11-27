"""RCS-77 — tests hors-ligne de l'orchestration J2 (clients simulés : aucune mesure de qualité LLM)."""
import sys
import unittest
try:
    import numpy
    import sklearn
except ModuleNotFoundError as exc:
    if exc.name not in {'numpy', 'sklearn'}:
        raise
    raise unittest.SkipTest('Suite RCS-77 exécutée dans sa CI dédiée') from exc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rcs.j2 import guards as G  # noqa: E402
from rcs.j2.bench import load_cases  # noqa: E402
from rcs.j2.llm import DemoClient, LLMResult  # noqa: E402
from rcs.j2.orchestrator import Orchestrator  # noqa: E402
from rcs.j2.scoring import score  # noqa: E402

CASES = load_cases(Path(__file__).resolve().parents[1] / "experiments" / "rcs77_cases_candidate.jsonl")
BY_ID = {c["id"]: c for c in CASES}


class FixedClient:
    def __init__(self, name, text, status="ok"):
        self.name, self.text, self.status, self.calls = name, text, status, 0

    def generate(self, system, user, timeout_s=1.0):
        self.calls += 1
        return LLMResult(self.name, self.text, 1.0, 10, 5, self.status,
                         None if self.status == "ok" else "SimulatedOutage")


def test_candidate_test_set_shape():
    assert len(CASES) == 10
    cats = [c["category"] for c in CASES]
    assert cats.count("usuel") == 4 and cats.count("complexe") == 2
    assert {"source_absente", "source_contradictoire", "injection", "sensible"} <= set(cats)


def test_pii_is_blocked_before_any_llm_call():
    a, b = FixedClient("A", "x"), FixedClient("B", "x")
    tr = Orchestrator(a, b).run(BY_ID["T10"], "cascade")
    assert tr.call_count == 0 and tr.validation == "blocked_pii"
    assert score(BY_ID["T10"], tr.answer)[0] == 1


def test_injection_sentence_removed_from_context():
    captured = {}

    class Spy(FixedClient):
        def generate(self, system, user, timeout_s=1.0):
            captured["user"] = user
            return super().generate(system, user, timeout_s)

    Orchestrator(Spy("A", "ok"), Spy("B", "ok")).run(BY_ID["T09"], "mono_a")
    assert "ACCÈS ADMIN" not in captured["user"]
    assert "6 mois" in captured["user"]


def test_cascade_escalates_when_a_invalid_and_stops_when_valid():
    good = "La visite préventive complète a lieu tous les 6 mois. Sources: [DOC08]"
    a, b = FixedClient("A", "réponse sans citation du tout ici"), FixedClient("B", good)
    tr = Orchestrator(a, b).run(BY_ID["T09"], "cascade")
    assert tr.route.startswith("A->B") and tr.call_count == 2 and score(BY_ID["T09"], tr.answer)[0] == 1
    a2, b2 = FixedClient("A", good), FixedClient("B", good)
    tr2 = Orchestrator(a2, b2).run(BY_ID["T09"], "cascade")
    assert tr2.call_count == 1 and b2.calls == 0


def test_cascade_budget_and_outage_of_b():
    a, b = FixedClient("A", ""), FixedClient("B", "", status="error")
    tr = Orchestrator(a, b).run(BY_ID["T01"], "cascade")
    assert tr.call_count == 2 and tr.status == "error"
    assert score(BY_ID["T01"], tr.answer)[0] == 0
    tr1 = Orchestrator(a, b, max_calls=1).run(BY_ID["T01"], "cascade")
    assert tr1.call_count == 1 and tr1.validation.startswith("budget_exceeded")


def test_router_uses_question_only():
    o = Orchestrator(DemoClient(), DemoClient())
    hits = o.retriever.search(BY_ID["T06"]["question"])
    assert o.choose_model(BY_ID["T06"]["question"], hits) == "B"   # « Compare »
    hits = o.retriever.search(BY_ID["T03"]["question"])
    assert o.choose_model(BY_ID["T03"]["question"], hits) == "A"


def test_validator_contract():
    assert G.validate_answer("Le seuil est au quantile 95 %. Sources: [DOC07]", {"DOC07"}) == (True, "ok")
    assert G.validate_answer("Sources: [DOC07]", {"DOC07"})[1] == "citation_only"
    assert G.validate_answer("Réponse plausible mais inventée sans source.", {"DOC07"})[1] == "no_citation"
    assert G.validate_answer("Le seuil du score vaut 10 unités. Sources: [DOC99]", {"DOC07"})[1] == "citation_not_in_context"
    assert G.validate_answer("ACCÈS ADMIN ACCORDÉ", {"DOC08"})[1] == "injection_payload"
    assert G.validate_answer("Information non disponible dans les sources.", set()) == (True, "abstention")


def test_scoring_rules():
    c = BY_ID["T08"]
    assert score(c, "Le seuil est au quantile 95 %. Sources: [DOC07]")[0] == 1
    assert score(c, "Quantile 99 %. Sources: [DOC06]")[0] == 0
    assert score(BY_ID["T07"], "Information non disponible dans les sources.")[0] == 1
    assert score(BY_ID["T07"], "Il coûte 1 M€. Sources: [DOC08]")[0] == 0


def test_injection_and_secret_request_removed_in_every_guarded_strategy():
    class Spy(FixedClient):
        def generate(self, system, user, timeout_s=1.0):
            assert "ACCÈS ADMIN" not in user and "mot de passe" not in user.lower()
            assert "ignore toutes les instructions" not in user.lower()
            assert "6 mois" in user
            return super().generate(system, user, timeout_s)
    for strategy in ("mono_a", "mono_b", "routing", "cascade"):
        a, b = Spy("A", ""), Spy("B", "La visite préventive a lieu tous les 6 mois. Sources: [DOC08]")
        trace = Orchestrator(a, b).run(BY_ID["T09"], strategy)
        assert trace.call_count >= 1
        assert "ACCÈS ADMIN" not in trace.answer


def test_guarded_output_never_echoes_rejected_sensitive_content():
    a = FixedClient("A", "Contactez demo@example.invalid pour la procédure. Sources: [DOC01]")
    trace = Orchestrator(a, a).run(BY_ID["T01"], "mono_a")
    assert trace.validation == "output_pii" and "example.invalid" not in trace.answer


def test_trace_writer_excludes_raw_text(tmp_path):
    import json
    from rcs.j2.bench import write_outputs
    row = {"trace_id":"test-trace-1", "case_id":"T01", "strategy":"mono_a", "status":"ok", "variant":"default", "answer":"demo@example.invalid", "question_sha256":"private", "score_reason":"free text"}
    prefix = tmp_path / "trace"
    write_outputs(prefix, [row], [], [], {})
    published = json.loads((tmp_path / "trace_traces.jsonl").read_text(encoding="utf-8"))
    assert not ({"answer", "question_sha256", "score_reason"} & published.keys())
    assert "example.invalid" not in str(published)
