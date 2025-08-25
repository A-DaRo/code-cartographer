from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ViewState:
    """
    A serializable Data Transfer Object (DTO) representing the result of a query.

    This object contains a simple, flat list of nodes and edges that constitute
    the requested view. It is completely decoupled from the Metamodel's complex
    object graph, making it suitable for serialization (e.g., to JSON) and
    consumption by any presentation layer.
    """
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)