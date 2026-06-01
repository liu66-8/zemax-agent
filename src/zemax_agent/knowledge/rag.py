from __future__ import annotations

import logging
from typing import Any, Optional

from zemax_agent.knowledge.qdrant_store import QdrantStore
from zemax_agent.knowledge.embeddings import OpticalEmbedder

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, store: QdrantStore):
        self._store = store

    def retrieve(
        self,
        query: str,
        collection_name: str = "knowledge_docs",
        top_k: int = 5,
        rerank: bool = True,
        filter_source_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        filter_cond = None
        if filter_source_type:
            filter_cond = {"source_type": filter_source_type}

        results = self._store.search(
            collection_name=collection_name,
            query=query,
            limit=top_k * 2 if rerank else top_k,
            filter_condition=filter_cond,
        )

        if rerank:
            results = self._rerank(query, results)[:top_k]

        return results

    def _rerank(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        def score(item: dict[str, Any]) -> float:
            base = item.get("score", 0.0)
            payload = item.get("payload", {})
            credibility = float(payload.get("credibility", 1.0))
            source_weight = {
                "official_doc": 1.2,
                "zos_api_doc": 1.2,
                "design_spec": 1.1,
                "project_case": 1.0,
                "external": 0.8,
                "ai_generated": 0.7,
            }.get(payload.get("source_type", ""), 1.0)
            return base * credibility * source_weight

        scored = [(score(r), r) for r in results]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    def inject_context(
        self,
        query: str,
        collection_name: str = "knowledge_docs",
        top_k: int = 5,
        format_type: str = "llm",
    ) -> str:
        results = self.retrieve(query, collection_name, top_k=top_k)

        if not results:
            return ""

        if format_type == "llm":
            parts = ["[Retrieved Knowledge Context]\n"]
            for i, r in enumerate(results, 1):
                payload = r.get("payload", {})
                source_title = payload.get("title", payload.get("source_title", "Unknown"))
                text = payload.get("text", "")[:800]
                parts.append(f"--- Source {i}: {source_title} (relevance: {r['score']:.3f}) ---")
                parts.append(text)
            return "\n".join(parts)

        if format_type == "compact":
            return "\n\n".join(
                r.get("payload", {}).get("text", "")[:500] for r in results
            )

        return str(results)

    def search_knowledge(
        self,
        query: str,
        top_k: int = 10,
        include_glass: bool = False,
    ) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}

        result["docs"] = self.retrieve(query, "knowledge_docs", top_k=top_k)
        result["cases"] = self.retrieve(query, "design_cases", top_k=min(top_k, 3))

        if include_glass:
            result["glass"] = self.retrieve(query, "glass_catalog", top_k=min(top_k, 5))

        return result
