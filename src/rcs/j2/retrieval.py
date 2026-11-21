"""Recherche documentaire TF-IDF sur le corpus autorisé (corpus/*.md), découpé par paragraphe."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from rcs import CORPUS

FR_STOP = set("""le la les un une des de du d l et ou à au aux en dans par pour sur avec sans ce cette ces est sont
qui que quoi quel quelle quels quelles comment pourquoi il elle ils elles on ne pas plus se sa son ses leur leurs
y a été être fait faire doit peut entre lors si""".split())


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


@dataclass
class Chunk:
    doc_id: str
    title: str
    text: str


@dataclass
class Hit:
    chunk: Chunk
    score: float


def load_chunks(corpus_dir: Path = CORPUS) -> list[Chunk]:
    chunks = []
    for p in sorted(corpus_dir.glob("DOC*.md")):
        doc_id = p.name.split("_")[0]
        lines = p.read_text(encoding="utf-8").strip().split("\n")
        title = lines[0].lstrip("# ").strip()
        for para in re.split(r"\n\s*\n", "\n".join(lines[1:])):
            para = para.strip()
            if para:
                chunks.append(Chunk(doc_id, title, para))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk] | None = None):
        self.chunks = chunks or load_chunks()
        # le titre est concaténé pour donner du contexte (n° de version, nom du mode, etc.)
        docs = [_norm(c.title + " " + c.text) for c in self.chunks]
        self.vec = TfidfVectorizer(stop_words=sorted(FR_STOP), ngram_range=(1, 2), sublinear_tf=True)
        self.mat = self.vec.fit_transform(docs)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        q = self.vec.transform([_norm(query)])
        sims = (self.mat @ q.T).toarray().ravel()
        order = np.argsort(-sims)[:k]
        return [Hit(self.chunks[i], float(sims[i])) for i in order]
