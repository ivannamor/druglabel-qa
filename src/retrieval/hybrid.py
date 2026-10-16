"""Retrieval entry point: vector, graph or hybrid, chosen by RETRIEVAL_MODE.

Hybrid = graph passages first (they answer the relational part of a question: which drugs, which
interactions), then vector passages (they cover wording the graph does not model), without duplicates.
"""

from src.retrieval.graph import GraphFact
from src.retrieval.graph import search as graph_search
from src.retrieval.vector import RetrievedChunk, get_retriever
from src.settings import get_settings
from src.tracing import langfuse, observe


@observe(name="retrieve", as_type="retriever", capture_output=False)
def retrieve(question: str) -> tuple[list[RetrievedChunk], list[GraphFact]]:
    s = get_settings()
    vector = (get_retriever().search(question, s.top_k, s.dedup_threshold)
              if s.retrieval_mode in ("vector", "hybrid") else [])
    graph, facts = (graph_search(question, s.graph_max_passages)
                    if s.retrieval_mode in ("graph", "hybrid") else ([], []))
    merged = list({c.chunk_id: c for c in reversed(graph + vector)}.values())[::-1]  # first occurrence wins
    langfuse().update_current_span(
        output=[{"chunk_id": c.chunk_id, "drug": c.drug, "section": c.section, "score": round(c.score, 3)}
                for c in merged],
        metadata={"mode": s.retrieval_mode, "vector_passages": len(vector), "graph_passages": len(graph),
                  "graph_facts": len(facts)})
    return merged, facts
