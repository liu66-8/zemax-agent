from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class KnowledgeSourceType(str, Enum):
    MANUAL = "manual"
    OFFICIAL_DOC = "official_doc"
    ZOS_API_DOC = "zos_api_doc"
    DESIGN_SPEC = "design_spec"
    PROJECT_CASE = "project_case"
    EXTERNAL = "external"
    AI_GENERATED = "ai_generated"


class KnowledgeSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: KnowledgeSourceType = KnowledgeSourceType.MANUAL
    title: str = ""
    description: str = ""
    source_path: str = ""
    collection_name: str = "knowledge_docs"
    credibility: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    chunk_count: int = 0


class DocumentChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_index: int = 0
    source_id: str = ""
