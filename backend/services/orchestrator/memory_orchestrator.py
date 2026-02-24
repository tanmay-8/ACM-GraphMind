"""
Memory Orchestrator - Coordinates memory ingestion workflow.

Flow:
1. Extract entities from text (LLM)
2. Ingest into graph (Neo4j)
"""

from typing import Dict, Any
from services.extraction.llm_extractor import LLMExtractor
from services.graph.ingestion import GraphIngestion


class MemoryOrchestrator:
    """
    Orchestrates complete memory ingestion workflow.
    """
    
    def __init__(self):
        """Initialize all required services."""
        self.extractor = LLMExtractor()
        self.graph_ingestion = GraphIngestion()
    
    def ingest_memory(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Execute complete memory ingestion workflow.
        
        Args:
            user_id: User identifier
            message: User's message containing information to store
            
        Returns:
            Dictionary with ingestion results
        """
        # Step 1: Extract structured data from text
        extracted_data = self.extractor.extract(message, user_id)
        facts = extracted_data.get("facts", [])
        nodes = extracted_data.get("nodes", [])
        relationships = extracted_data.get("relationships", [])
        
        # Step 2: Ingest into graph (Message + Facts + Entities)
        graph_result = self.graph_ingestion.ingest_memory(
            user_id=user_id,
            message_text=message,
            facts=facts,
            nodes=nodes,
            relationships=relationships
        )
        
        # TODO: Implement vector ingestion for semantic search if needed
        
        return {
            "nodes_created": graph_result.get("nodes_created", 0),
            "relationships_created": graph_result.get("relationships_created", 0),
            "facts_created": graph_result.get("facts_created", 0),
            "chunks_indexed": 0  # No vector indexing in current implementation
        }
    
    def close(self):
        """Close all service connections."""
        self.graph_ingestion.close()
