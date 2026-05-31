from __future__ import annotations

import uuid
from typing import Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from zemax_agent.knowledge.embeddings import OpticalEmbedder


DEFAULT_COLLECTIONS = {
    "knowledge_docs": "知识文档集合 - OpticStudio 文档、ZOS-API 文档、设计规范、外部资料",
    "design_cases": "设计案例集合 - 历史项目案例、设计经验",
    "glass_catalog": "玻璃材料目录集合 - 光学玻璃材料特性与检索",
}


class QdrantStore:
    def __init__(self, url: str = "http://192.168.121.158:6333", prefer_grpc: bool = False, embedder: Optional[OpticalEmbedder] = None):
        self._url = url
        self._client = QdrantClient(url=url, prefer_grpc=prefer_grpc)
        self._embedder = embedder or OpticalEmbedder()

    def ensure_collections(self) -> None:
        for name in DEFAULT_COLLECTIONS:
            self._ensure_collection(name)

    def _ensure_collection(self, name: str) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if name not in existing:
            self._client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=self._embedder.vector_size,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def delete_collection(self, name: str) -> bool:
        existing = {c.name for c in self._client.get_collections().collections}
        if name not in existing:
            return False
        self._client.delete_collection(collection_name=name)
        return True

    def upsert(
        self,
        collection_name: str,
        documents: list[str],
        metadata: Optional[list[dict[str, Any]]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        embeddings = self._embedder.encode(documents)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadata is None:
            metadata = [{} for _ in documents]

        points = []
        for i, (pid, vec, doc, meta) in enumerate(zip(ids, embeddings, documents, metadata)):
            payload = {"text": doc, **meta}
            points.append(qmodels.PointStruct(id=pid, vector=vec, payload=payload))

        self._client.upsert(collection_name=collection_name, points=points)
        return ids

    def delete(self, collection_name: str, point_ids: list[str]) -> None:
        self._client.delete(collection_name=collection_name, points_selector=qmodels.PointIdsList(points=point_ids))

    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_condition: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        vector = self._embedder.encode_query(query)
        query_filter = None
        if filter_condition:
            conditions = []
            for key, value in filter_condition.items():
                conditions.append(
                    qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=value))
                )
            if conditions:
                query_filter = qmodels.Filter(must=conditions)

        results = self._client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    def scroll(
        self,
        collection_name: str,
        limit: int = 100,
        offset: Optional[str] = None,
    ) -> tuple[list[dict[str, Any]], Optional[str]]:
        points, next_offset = self._client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        records = [
            {"id": p.id, "payload": p.payload}
            for p in points
        ]
        return records, next_offset

    def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        info = self._client.get_collection(collection_name=collection_name)
        return {
            "name": collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": info.status.name,
        }

    def list_collections(self) -> list[str]:
        return [c.name for c in self._client.get_collections().collections]

    def close(self) -> None:
        self._client.close()

    @property
    def embedder(self) -> OpticalEmbedder:
        return self._embedder
