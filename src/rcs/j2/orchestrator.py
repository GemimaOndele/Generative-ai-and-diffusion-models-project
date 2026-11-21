"""Orchestrateur J2 : B0 extractif, mono-A, mono-B, routing A/B, cascade A→B bornée.

Modèle A = petit modèle économique ; modèle B = modèle plus robuste. Les garde-fous (guards.py)
s'appliquent à l'identique à toutes les stratégies ; l'ablation `guards=False` les désactive.
La décision de routage n'utilise QUE la question et le résultat de recherche (jamais la réponse attendue).
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field, asdict

from . import guards as G
from .llm import SYSTEM_PROMPT, LLMResult, build_user_prompt
from .retrieval import Retriever

COMPLEX_MARKERS = ("pourquoi", "compar", "différence", "difference", "expliqu", "versus", " vs ", "avantage",
                   "justifi", "impact")
ABSTAIN_TEXT = "Information non disponible dans les sources."
HUMAN_TEXT = "Question bloquée : revue humaine requise (données personnelles ou contrôle échoué)."
STRATEGIES = ("b0_extractive", "mono_a", "mono_b", "mono_b_norag", "routing", "cascade")


@dataclass
class Trace:
    trace_id: str
    case_id: str
    category: str
    strategy: str
    question_sha256: str
    route: str | None = None
    models: list[str] = field(default_factory=list)
    call_count: int = 0
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "ok"
    error_type: str | None = None
    validation: str | None = None
    guard_events: list[str] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    answer: str = ""
    cost_eur: float | None = None  # local : pas de coût API ; voir TP05 pour l'estimation

    def to_dict(self) -> dict:
        return asdict(self)


class Orchestrator:
    def __init__(self, model_a, model_b, retriever: Retriever | None = None, k: int = 3,
                 use_guards: bool = True, max_calls: int = 2, complexity_words: int = 18,
                 timeout_a: float = 60.0, timeout_b: float = 90.0):
        self.a, self.b = model_a, model_b
        self.retriever = retriever or Retriever()
        self.k = k
        self.use_guards = use_guards
        self.max_calls = max_calls
        self.complexity_words = complexity_words
        self.timeout_a, self.timeout_b = timeout_a, timeout_b

    # ---------- étapes communes ----------
    def choose_model(self, question: str, hits) -> str:
        q = question.lower()
        if any(m in q for m in COMPLEX_MARKERS) or len(question.split()) > self.complexity_words:
            return "B"
        top = hits[0].score if hits else 0.0
        close_docs = {h.chunk.doc_id for h in hits if top and h.score >= 0.7 * top}
        return "B" if len(close_docs) >= 3 else "A"

    def _prepare(self, question: str, tr: Trace):
        if self.use_guards:
            pii = G.detect_pii(question)
            if pii:
                tr.guard_events.append("pii_blocked:" + ",".join(pii))
                return None, set()
        hits = self.retriever.search(question, self.k)
        tr.retrieved = [f"{h.chunk.doc_id}:{h.score:.3f}" for h in hits]
        if self.use_guards and (not hits or hits[0].score < G.MIN_RETRIEVAL_SCORE):
            tr.guard_events.append("out_of_scope_low_retrieval")
            return [], set()
        texts = [h.chunk.text for h in hits]
        if self.use_guards:
            texts, removed = G.sanitize_passages(texts)
            if removed:
                tr.guard_events.append(f"injection_sentences_removed:{removed}")
        passages = [(h.chunk.doc_id, t) for h, t in zip(hits, texts)]
        return (passages, hits), {h.chunk.doc_id for h in hits}

    def _call(self, model, user: str, tr: Trace, timeout: float) -> LLMResult:
        res = model.generate(SYSTEM_PROMPT, user, timeout_s=timeout)
        tr.models.append(res.model)
        tr.call_count += 1
        tr.latency_ms += res.latency_ms
        tr.input_tokens += res.input_tokens or 0
        tr.output_tokens += res.output_tokens or 0
        if res.status != "ok":
            tr.status, tr.error_type = res.status, res.error_type
        return res

    # ---------- exécution ----------
    def run(self, case: dict, strategy: str) -> Trace:
        if strategy not in STRATEGIES:
            raise ValueError(strategy)
        q = case["question"]
        tr = Trace(uuid.uuid4().hex[:8], case["id"], case.get("category", ""), strategy,
                   hashlib.sha256(q.encode()).hexdigest()[:16])
        t0 = time.perf_counter()
        prep, allowed = self._prepare(q, tr)
        if prep is None:
            tr.answer, tr.validation = HUMAN_TEXT, "blocked_pii"
        elif prep == []:
            tr.answer, tr.validation = ABSTAIN_TEXT, "abstention_guard"
        else:
            passages, hits = prep
            user = build_user_prompt(q, passages)
            if strategy == "b0_extractive":
                doc, txt = passages[0]
                tr.answer, tr.route = f"{txt} Sources: [{doc}]", "none"
                tr.validation = "ok"
            elif strategy == "mono_b_norag":  # ablation TP03 : même modèle, sans passages (pas de RAG)
                tr.route = "B"
                res = self._call(self.b, f"Question: {q}\nRéponse:", tr, self.timeout_b)
                self._finalize(tr, res.text, allowed)
            elif strategy in ("mono_a", "mono_b"):
                model, to = (self.a, self.timeout_a) if strategy == "mono_a" else (self.b, self.timeout_b)
                tr.route = strategy[-1].upper()
                res = self._call(model, user, tr, to)
                self._finalize(tr, res.text, allowed)
            elif strategy == "routing":
                tr.route = self.choose_model(q, hits)
                model, to = (self.a, self.timeout_a) if tr.route == "A" else (self.b, self.timeout_b)
                res = self._call(model, user, tr, to)
                self._finalize(tr, res.text, allowed)
            else:  # cascade A -> B bornée
                tr.route = "A"
                res = self._call(self.a, user, tr, self.timeout_a)
                ok, reason = G.validate_answer(res.text, allowed) if self.use_guards else (bool(res.text), "noguard")
                if ok:
                    tr.answer, tr.validation = res.text, reason
                elif tr.call_count >= self.max_calls:
                    tr.answer, tr.validation = HUMAN_TEXT, f"budget_exceeded_after:{reason}"
                else:
                    tr.route = f"A->B({reason})"
                    tr.status, tr.error_type = "ok", None  # l'échec de A est rattrapé par B
                    res_b = self._call(self.b, user, tr, self.timeout_b)
                    self._finalize(tr, res_b.text, allowed)
        tr.latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        return tr

    def _finalize(self, tr: Trace, text: str, allowed: set[str]) -> None:
        if not self.use_guards:
            tr.answer, tr.validation = text, "noguard"
            return
        ok, reason = G.validate_answer(text, allowed)
        tr.validation = reason
        # sortie invalide : on la conserve pour l'analyse mais on signale un refus explicite
        tr.answer = text if ok else f"[REFUS VALIDATEUR:{reason}] {text}"
