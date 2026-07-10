from typing import List, Optional
from pydantic import BaseModel

class GeniusMindMapRequest(BaseModel):
    topic: str

class GeniusMindMapNode(BaseModel):
    id: str
    title: str
    note: str
    x: int
    y: int

class GeniusMindMapEdge(BaseModel):
    source: str
    target: str

class GeniusMindMapResponse(BaseModel):
    success: bool
    nodes: List[GeniusMindMapNode]
    edges: List[GeniusMindMapEdge]
