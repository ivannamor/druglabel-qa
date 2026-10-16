"""Retrieval entry point: vector, graph or hybrid, chosen by RETRIEVAL_MODE.

Hybrid = graph passages first (they answer the relational part of a question: which drugs, which
interactions), then vector passages (they cover wording the graph does not model), without duplicates.
"""

from src.retrieval.graph import GraphFact
from src.retrieval.graph import search as graph_search
from src.retrieval.vector import RetrievedChunk, get_retriever
from src.settings import get_settings


def retrieve(question: str) -> tuple[list[RetrievedChunk], list[GraphFact]]:
    s = get_settings()
    vector = (get_retriever().search(question, s.top_k, s.dedup_threshold)
              if s.retrieval_mode in ("vector", "hybrid") else [])
    graph, facts = (graph_search(question, s.graph_max_passages)
                    if s.retrieval_mode in ("graph", "hybrid") else ([], []))
    merged = list({c.chunk_id: c for c in reversed(graph + vector)}.values())[::-1]  # first occurrence wins
    return merged, facts
