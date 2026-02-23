"""
Memory Mindmap Models - For graph visualization
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class MindmapNode(BaseModel):
    """Node in the mindmap graph."""
    id: str
    type: str
    label: str
    properties: Dict[str, Any] = {}


class MindmapEdge(BaseModel):
    """Edge/relationship in the mindmap graph."""
    id: str
    source: str
    target: str
    type: str
    label: str
    properties: Dict[str, Any] = {}


class MindmapResponse(BaseModel):
    """Response containing nodes and edges for visualization."""
    nodes: List[MindmapNode]
    edges: List[MindmapEdge]
    total_nodes: int
    total_edges: int
