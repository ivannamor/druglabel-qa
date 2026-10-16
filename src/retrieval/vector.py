"""Vector retrieval: exact cosine similarity over the Gold snapshot.

~14k chunks fit in memory, so a full numpy dot product (milliseconds) replaces a vector database
and is exact rather than approximate. Swapping in Databricks Vector Search would change only this module.

Duplicates are common: generic labels copy the brand label, so one passage can appear in up to 10 labels
of the same drug, verbatim or with small wording changes ("ELIQUIS is…" / "Apixaban is…"). Two steps:
1. Identical text (same `text_hash`) within a drug: only the copy from the most recent label is searchable.
2. Near-identical results (same drug, same section, cosine >= dedup_threshold) collapse into one result,
   represented by the most recent label, so the top_k results carry different information.
Copies are grouped per drug, never across drugs, so boilerplate shared by two drugs still returns each
drug's own label. `n_labels` reports how many labels hold the passage, so nothing is silently dropped.

Usage (from repo root): python -m src.retrieval.vector "What are the contraindications of apixaban?"
"""

import hashlib
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastembed import TextEmbedding

from src.settings import get_settings


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    label_id: str
    effective_time: str
    drug: str
    section: str
    subsection: str | None
    text: str
    score: float  # cosine similarity between question and passage, -1..1 (best copy)
    n_labels: int  # labels of this drug holding this passage verbatim or near-identical


class VectorRetriever:
    def __init__(self, snapshot_path: Path, embedding_model: str) -> None:
        self.snapshot_sha256 = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()  # exact file used, for run logs
        gold = pd.read_parquet(snapshot_path)
        snapshot_model = gold["embedding_model"].iloc[0]
        if snapshot_model != embedding_model:  # questions and chunks must be embedded by the same model
            raise ValueError(f"snapshot embedded with {snapshot_model}, settings say {embedding_model}")

        # One searchable row per (drug, passage): the copy from the most recent label.
        gold["n_labels"] = gold.groupby(["drug", "text_hash"])["label_id"].transform("nunique")
        gold = (gold.sort_values(["effective_time", "label_id"], ascending=False)
                .drop_duplicates(["drug", "text_hash"])
                .reset_index(drop=True))

        self.matrix = np.vstack(gold["embedding"].to_numpy()).astype(np.float32)
        self.chunks = gold.drop(columns="embedding")
        self.model = TextEmbedding(embedding_model)
        self.gold_version = int(gold["gold_delta_version"].iloc[0])
        self.silver_version = int(gold["silver_delta_version"].iloc[0])

    def search(self, question: str, top_k: int, dedup_threshold: float = 0.95) -> list[RetrievedChunk]:
        """The top_k distinct passages closest to the question, best first."""
        q = np.array(next(iter(self.model.query_embed([question]))), dtype=np.float32)
        scores = self.matrix @ q  # embeddings are normalized, so dot product = cosine similarity
        drug, section = self.chunks["drug"].to_numpy(), self.chunks["section"].to_numpy()
        recency = self.chunks["effective_time"].to_numpy()

        picked: list[int] = []  # row of the representative copy, in score order
        best_score: dict[int, float] = {}
        n_labels: dict[int, int] = {}
        for i in np.argsort(-scores)[: top_k * 100]:  # candidates: enough to skip up to ~10 copies per passage
            same = next((p for p in picked if drug[p] == drug[i] and section[p] == section[i]
                         and self.matrix[p] @ self.matrix[i] >= dedup_threshold), None)
            if same is None:
                if len(picked) < top_k:
                    picked.append(i)
                    best_score[i], n_labels[i] = float(scores[i]), int(self.chunks["n_labels"].iat[i])
                continue
            n_labels[same] += int(self.chunks["n_labels"].iat[i])
            if recency[i] > recency[same]:  # the most recent label represents the passage
                picked[picked.index(same)] = i
                best_score[i], n_labels[i] = best_score.pop(same), n_labels.pop(same)

        rows = self.chunks.iloc[picked]
        return [
            RetrievedChunk(
                chunk_id=row.chunk_id,
                label_id=row.label_id,
                effective_time=row.effective_time,
                drug=row.drug,
                section=row.section,
                subsection=row.subsection if isinstance(row.subsection, str) else None,
                text=row.text,
                score=best_score[i],
                n_labels=n_labels[i],
            )
            for i, row in zip(picked, rows.itertuples())
        ]


@lru_cache
def get_retriever() -> VectorRetriever:
    """Process-wide retriever for the Gold version in settings (loading the model takes a few seconds)."""
    s = get_settings()
    return VectorRetriever(s.gold_snapshot_path, s.embedding_model)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What are the contraindications of apixaban?"
    retriever = get_retriever()
    print(f"{len(retriever.chunks)} searchable passages (Gold v{retriever.gold_version})\n")
    for c in retriever.search(question, get_settings().top_k, get_settings().dedup_threshold):
        print(f"{c.score:.3f}  {c.chunk_id}  [{c.drug} · {c.section} {c.subsection or ''}] in {c.n_labels} label(s)")
        print(f"       {c.text[:160]}…\n")
