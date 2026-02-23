from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse, IntentType, MemoryStorageResult, RetrievalMetrics, SourceNode
from services.llm.intent_classifier import IntentClassifier
from services.orchestrator.memory_orchestrator import MemoryOrchestrator
from services.orchestrator.retrieval_orchestrator import RetrievalOrchestrator

router = APIRouter()

# Initialize services
intent_classifier = IntentClassifier()
memory_orchestrator = MemoryOrchestrator()
retrieval_orchestrator = RetrievalOrchestrator()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Unified chat endpoint supporting:
    - Memory ingestion (MEMORY)
    - Question answering (QUESTION)
    - Both operations (BOTH)
    """
    # Step 1: Classify intent
    intent = intent_classifier.classify(request.message)
    
    if intent == "MEMORY":
        # Handle memory ingestion only
        storage_result = memory_orchestrator.ingest_memory(
            user_id=request.user_id,
            message=request.message
        )
        
        return ChatResponse(
            intent=IntentType.MEMORY,
            memory_storage=MemoryStorageResult(**storage_result),
            message="Financial memory stored successfully."
        )
    
    elif intent == "QUESTION":
        # Handle query retrieval and answer generation
        answer, metrics, sources = retrieval_orchestrator.retrieve_and_answer(
            user_id=request.user_id,
            query=request.message
        )
        
        return ChatResponse(
            intent=IntentType.QUESTION,
            answer=answer,
            retrieval_metrics=RetrievalMetrics(**metrics),
            sources=sources,
            message="Answer generated successfully."
        )
    
    elif intent == "BOTH":
        # Handle both memory ingestion and query
        storage_result = memory_orchestrator.ingest_memory(
            user_id=request.user_id,
            message=request.message
        )
        
        answer, metrics, sources = retrieval_orchestrator.retrieve_and_answer(
            user_id=request.user_id,
            query=request.message
        )
        
        return ChatResponse(
            intent=IntentType.BOTH,
            answer=answer,
            memory_storage=MemoryStorageResult(**storage_result),
            retrieval_metrics=RetrievalMetrics(**metrics),
            sources=sources,
            message="Memory stored and answer generated."
        )
