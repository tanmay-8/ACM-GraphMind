from pydantic import BaseModel
from typing import Optional, List, Any
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
    """Detailed metrics for retrieval and generation performance"""
    graph_query_ms: float
    vector_search_ms: float
    context_assembly_ms: float
    retrieval_ms: float
    llm_generation_ms: float


class MemoryCitation(BaseModel):
    """Memory citation with retrieval score for explainability"""
    node_type: str
    retrieval_score: float
    hop_distance: Any  # Can be int or "N/A"
    snippet: str
    properties: dict
    score_breakdown: Optional[dict] = None  # graph_distance, recency, confidence, reinforcement


class MemoryStorageResult(BaseModel):
    """Result of memory storage operation"""
    nodes_created: int
    relationships_created: int
    facts_created: int
    chunks_indexed: int


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    intent: IntentType
    answer: Optional[str] = None
    memory_storage: Optional[MemoryStorageResult] = None
    retrieval_metrics: Optional[RetrievalMetrics] = None
    memory_citations: Optional[List[MemoryCitation]] = None
    message: str
