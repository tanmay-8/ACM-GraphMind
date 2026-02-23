"""
Graph Retrieval Service - Multi-hop graph queries with adaptive depth.

Handles:
- Adaptive retrieval depth based on query complexity
- Multi-hop graph traversal
- Performance measurement
- User isolation
"""

from typing import Dict, List, Any, Tuple
import time
from neo4j import GraphDatabase
from neo4j.time import DateTime
from config.settings import Settings


class GraphRetrieval:
    """
    Handles retrieval of data from Neo4j graph.
    Implements adaptive multi-hop retrieval.
    """
    
    def __init__(self):
        """Initialize Neo4j connection."""
        try:
            self.driver = GraphDatabase.driver(
                Settings.NEO4J_URI,
                auth=(Settings.NEO4J_USER, Settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j: {e}")
            self.driver = None
    
    def retrieve(
        self, 
        user_id: str, 
        query: str, 
        max_depth: int = 2
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Retrieve relevant graph context for a query.
        
        Args:
            user_id: User identifier
            query: User's query text
            max_depth: Maximum number of hops (default: 2)
            
        Returns:
            Tuple of (retrieved_nodes, retrieval_time_ms)
        """
        if not self.driver:
            print("Warning: Neo4j driver not initialized, returning empty results")
            return [], 0.0
        
        start_time = time.time()
        retrieved_nodes = []
        
        try:
            with self.driver.session() as session:
                # Determine optimal depth based on query
                depth = min(self._determine_query_depth(query), max_depth)
                
                # Execute retrieval query
                result = self._execute_retrieval_query(
                    session, user_id, query, depth
                )
                
                # Format results
                retrieved_nodes = self._format_results(result)
        
        except Exception as e:
            print(f"Error during graph retrieval: {e}")
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        return retrieved_nodes, retrieval_time_ms
    
    def _execute_retrieval_query(
        self, 
        session, 
        user_id: str, 
        query: str, 
        max_depth: int
    ):
        """
        Execute the graph retrieval query.
        
        Strategy:
        - Simple queries: 1 hop (direct connections)
        - Complex queries: 2-3 hops (multi-hop reasoning)
        - Updates last_reinforced on retrieved nodes (reinforcement learning)
        """
        # Retrieval query with reinforcement update
        simple_query = f"""
        MATCH (u:User {{id: $user_id}})
        OPTIONAL MATCH path = (u)-[r*1..{max_depth}]-(n)
        WHERE u.id = $user_id
        WITH u, collect(DISTINCT n) as nodes, collect(DISTINCT r) as rels
        
        // Update last_reinforced on all retrieved nodes (reinforcement learning)
        FOREACH (node IN nodes | 
            SET node.last_reinforced = datetime()
        )
        
        RETURN u, nodes, rels
        """
        
        try:
            result = session.run(simple_query, user_id=user_id)
            return list(result)
        except Exception as e:
            print(f"Query execution failed: {e}")
            return []
    
    def _serialize_neo4j_types(self, obj: Any) -> Any:
        """Convert Neo4j types to JSON-serializable Python types."""
        if isinstance(obj, DateTime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_neo4j_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_neo4j_types(item) for item in obj]
        else:
            return obj
    
    def _format_results(self, result) -> List[Dict[str, Any]]:
        """
        Format Neo4j results into structured dictionaries.
        """
        formatted_nodes = []
        
        try:
            for record in result:
                # User node
                user_node = record.get("u")
                if user_node:
                    formatted_nodes.append({
                        "type": list(user_node.labels)[0] if user_node.labels else "User",
                        "properties": self._serialize_neo4j_types(dict(user_node))
                    })
                
                # Connected nodes
                nodes = record.get("nodes", [])
                for node in nodes:
                    if node:  # Skip None values
                        formatted_nodes.append({
                            "type": list(node.labels)[0] if node.labels else "Entity",
                            "properties": self._serialize_neo4j_types(dict(node))
                        })
                
                # Relationships (stored in node context)
                rels = record.get("rels", [])
                for rel_list in rels:
                    if rel_list:  # rel_list might be a list of relationships
                        # Handle case where rels is a list of relationship lists
                        if isinstance(rel_list, list):
                            for rel in rel_list:
                                if rel:
                                    formatted_nodes.append({
                                        "type": "Relationship",
                                        "relationship_type": rel.type,
                                        "properties": self._serialize_neo4j_types(dict(rel))
                                    })
                        elif hasattr(rel_list, 'type'):  # Single relationship
                            formatted_nodes.append({
                                "type": "Relationship",
                                "relationship_type": rel_list.type,
                                "properties": self._serialize_neo4j_types(dict(rel_list))
                            })
        
        except Exception as e:
            print(f"Error formatting results: {e}")
        
        return formatted_nodes
    
    def _determine_query_depth(self, query: str) -> int:
        """
        Determine retrieval depth based on query complexity.
        
        Simple (1 hop): "What assets do I own?"
        Complex (2-3 hops): "Am I aligned with my retirement goal?"
        """
        query_lower = query.lower()
        
        # Keywords indicating complex multi-hop reasoning
        complex_keywords = [
            "aligned", "compare", "why", "how am i", "goal",
            "progress", "relationship", "between", "impact",
            "affect", "contributing", "towards"
        ]
        
        # Very complex queries need deeper traversal
        very_complex_keywords = [
            "overall", "portfolio", "all", "total", "complete",
            "entire", "comprehensive"
        ]
        
        if any(keyword in query_lower for keyword in very_complex_keywords):
            return 3  # Very complex query
        elif any(keyword in query_lower for keyword in complex_keywords):
            return 2  # Complex query
        else:
            return 1  # Simple query
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
