from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class IntentType(str, Enum):
    """Intent classification for chat requests"""
    MEMORY = "MEMORY"
    QUESTION = "QUESTION"
    BOTH = "BOTH"


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    user_id: str
    message: str
    conversation_id: Optional[str] = None


class RetrievalMetrics(BaseModel):
    """Metrics for retrieval and generation performance"""
    retrieval_ms: float
    llm_generation_ms: float


class SourceNode(BaseModel):
    """Source node for explainability"""
    node_type: str
    properties: dict


class MemoryStorageResult(BaseModel):
    """Result of memory storage operation"""
    nodes_created: int
    relationships_created: int
    chunks_indexed: int


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    intent: IntentType
    answer: Optional[str] = None
    memory_storage: Optional[MemoryStorageResult] = None
    retrieval_metrics: Optional[RetrievalMetrics] = None
    sources: Optional[List[SourceNode]] = None
    message: str
