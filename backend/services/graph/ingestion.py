"""
Graph Ingestion Service - Store structured data in Neo4j.

Handles:
- Node creation with user isolation
- Relationship creation
- Duplicate detection (MERGE logic)
- Performance tracking
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from neo4j import GraphDatabase
from config.settings import Settings


class GraphIngestion:
    """
    Handles ingestion of structured data into Neo4j graph.
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
    
    def ingest_memory(
        self, 
        user_id: str, 
        nodes: List[Dict[str, Any]], 
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Ingest nodes and relationships into the graph.
        
        Args:
            user_id: User identifier
            nodes: List of node dictionaries
            relationships: List of relationship dictionaries
            
        Returns:
            Dictionary with counts of nodes and relationships created
        """
        if not self.driver:
            print("Warning: Neo4j driver not initialized, skipping ingestion")
            return {"nodes_created": 0, "relationships_created": 0}
        
        nodes_created = 0
        relationships_created = 0
        
        try:
            with self.driver.session() as session:
                # 1. Ensure User node exists
                self._ensure_user_node(session, user_id)
                
                # 2. Create/merge nodes
                for node in nodes:
                    self._merge_node(session, user_id, node)
                    nodes_created += 1
                
                # 3. Create/merge relationships
                for rel in relationships:
                    self._merge_relationship(session, user_id, rel)
                    relationships_created += 1
        
        except Exception as e:
            print(f"Error during graph ingestion: {e}")
            raise
        
        return {
            "nodes_created": nodes_created,
            "relationships_created": relationships_created
        }
    
    def _ensure_user_node(self, session, user_id: str):
        """Ensure a User node exists for the given user_id."""
        query = """
        MERGE (u:User {id: $user_id})
        SET u.last_active = datetime()
        RETURN u
        """
        session.run(query, user_id=user_id)
    
    def _merge_node(self, session, user_id: str, node: Dict[str, Any]):
        """
        Merge a single node into the graph.
        
        Uses MERGE to avoid duplicates.
        Adds user_id, metadata, and reinforcement fields automatically.
        """
        node_type = node.get("type", "Entity")
        properties = node.get("properties", {})
        
        # Ensure node has an ID
        if "id" not in properties:
            properties["id"] = f"{node_type.lower()}_{uuid.uuid4().hex[:8]}"
        
        # Add user_id for isolation
        properties["user_id"] = user_id
        
        # Add metadata fields if not present
        if "source_type" not in properties:
            properties["source_type"] = "user_input"
        
        # Create Cypher query with labels and metadata
        query = f"""
        MERGE (n:{node_type} {{id: $id, user_id: $user_id}})
        ON CREATE SET 
            n.created_at = datetime(),
            n.timestamp = datetime(),
            n.confidence = 0.8,
            n.last_reinforced = datetime()
        SET n += $properties, 
            n.updated_at = datetime()
        RETURN n
        """
        
        session.run(
            query,
            id=properties["id"],
            user_id=user_id,
            properties=properties
        )
    
    def _merge_relationship(self, session, user_id: str, relationship: Dict[str, Any]):
        """
        Merge a relationship between two nodes.
        
        Ensures both nodes exist before creating relationship.
        """
        rel_type = relationship.get("type", "RELATED_TO")
        from_type = relationship.get("from_type", "Entity")
        to_type = relationship.get("to_type", "Entity")
        from_name = relationship.get("from_name")
        to_name = relationship.get("to_name")
        properties = relationship.get("properties", {})
        
        # If from_type is User, match by user_id
        if from_type == "User":
            from_match = f"(a:User {{id: $user_id}})"
            from_params = {"user_id": user_id}
        else:
            from_match = f"(a:{from_type} {{name: $from_name, user_id: $user_id}})"
            from_params = {"from_name": from_name, "user_id": user_id}
        
        # Match target node
        to_match = f"(b:{to_type} {{name: $to_name, user_id: $user_id}})"
        to_params = {"to_name": to_name, "user_id": user_id}
        
        # Build relationship query
        query = f"""
        MATCH {from_match}
        MATCH {to_match}
        MERGE (a)-[r:{rel_type}]->(b)
        ON CREATE SET r.created_at = datetime()
        SET r += $properties, r.updated_at = datetime()
        RETURN r
        """
        
        params = {**from_params, **to_params, "properties": properties}
        
        try:
            session.run(query, **params)
        except Exception as e:
            print(f"Warning: Could not create relationship {rel_type}: {e}")
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
