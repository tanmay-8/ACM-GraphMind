"""
Retrieval Orchestrator - Coordinates query retrieval and answer generation.

Flow:
1. Classify query complexity
2. Retrieve from graph (adaptive depth)
3. Assemble context
4. Generate answer using LLM

TODO: Add vector retrieval when implemented
"""

from typing import Dict, Any, List, Tuple
import time
from services.graph.retrieval import GraphRetrieval
from services.llm.answer_generator import AnswerGenerator


class RetrievalOrchestrator:
    """
    Orchestrates complete query retrieval and answer generation workflow.
    Currently uses graph-only retrieval.
    """
    
    def __init__(self):
        """Initialize all required services."""
        self.graph_retrieval = GraphRetrieval()
        self.answer_generator = AnswerGenerator()
        # TODO: Add vector retrieval and embedding services when needed
    
    def retrieve_and_answer(
        self, 
        user_id: str, 
        query: str
    ) -> Tuple[str, Dict[str, float], List[Dict[str, Any]]]:
        """
        Execute complete retrieval and answer generation workflow.
        
        Args:
            user_id: User identifier
            query: User's question
            
        Returns:
            Tuple of (answer, metrics, sources)
        """
        # Step 1: Retrieve from graph
        graph_context, graph_time = self.graph_retrieval.retrieve(
            user_id=user_id,
            query=query,
            max_depth=2  # Adaptive based on query complexity
        )
        
        # TODO: Step 2 - Vector retrieval (when implemented)
        # query_embedding = self.embedding_service.embed_text(query)
        # vector_context, vector_time = self.vector_retrieval.retrieve(
        #     user_id=user_id,
        #     query_embedding=query_embedding,
        #     top_k=5
        # )
        vector_context = []
        vector_time = 0.0
        
        # Step 3: Generate answer using graph context (with timing)
        llm_start = time.time()
        answer = self.answer_generator.generate(
            query=query,
            graph_context=graph_context,
            vector_context=vector_context
        )
        llm_time_ms = (time.time() - llm_start) * 1000
        
        # Step 4: Assemble metrics
        metrics = {
            "retrieval_ms": graph_time + vector_time,
            "llm_generation_ms": llm_time_ms
        }
        
        # Step 5: Format sources for explainability
        sources = self._format_sources(graph_context, vector_context)
        
        return answer, metrics, sources
    
    def _format_sources(
        self, 
        graph_context: List[Dict[str, Any]], 
        vector_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format source nodes for explainability.
        
        Args:
            graph_context: Retrieved graph nodes
            vector_context: Retrieved vector chunks (currently unused)
            
        Returns:
            List of formatted source nodes
        """
        sources = []
        
        # Add graph nodes as sources
        for node in graph_context[:5]:  # Limit to top 5
            sources.append({
                "node_type": node.get("type", "Unknown"),
                "properties": node.get("properties", {})
            })
        
        # TODO: Add vector chunks when vector retrieval is implemented
        # for chunk in vector_context[:3]:
        #     sources.append({
        #         "node_type": "TextMemory",
        #         "properties": {"text": chunk.get("text", "")}
        #     })
        
        return sources
    
    def close(self):
        """Close all service connections."""
        self.graph_retrieval.close()
        # TODO: Close vector services when implemented

