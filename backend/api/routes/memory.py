"""
Memory/Mindmap Routes - Visualization endpoints
"""

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from api.models_mindmap import MindmapResponse, MindmapNode, MindmapEdge
from services.graph.mindmap_service import mindmap_service
from services.auth.auth_service import auth_service
from services.database.user_service import UserService

router = APIRouter()

# Initialize user service
user_service = UserService()


def get_user_from_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user_id from JWT token.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        user_id string
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload["user_id"]


@router.get("/mindmap", response_model=MindmapResponse)
async def get_mindmap(authorization: Optional[str] = Header(None)):
    """
    Get user's memory graph for visualization.
    
    Returns all nodes and edges for the authenticated user's
    knowledge graph, formatted for mindmap visualization.
    
    Args:
        authorization: JWT token in Authorization header
        
    Returns:
        MindmapResponse with nodes and edges
    """
    # Get PostgreSQL user_id from JWT token
    pg_user_id = get_user_from_token(authorization)
    
    # Get user's neo4j_user_id from PostgreSQL
    user = user_service.get_user_by_id(pg_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    neo4j_user_id = user["neo4j_user_id"]
    if not neo4j_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not linked to knowledge graph"
        )
    
    # Get graph data using neo4j_user_id
    nodes_data, edges_data = mindmap_service.get_user_graph(neo4j_user_id)
    
    # Convert to Pydantic models
    nodes = [MindmapNode(**node) for node in nodes_data]
    edges = [MindmapEdge(**edge) for edge in edges_data]
    
    return MindmapResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges)
    )
