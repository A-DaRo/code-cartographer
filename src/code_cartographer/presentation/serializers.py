from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..query_control.view_state import ViewState

class JsonSerializer:
    """
    A data serialization strategy that transforms a ViewState DTO into a
    JSON-serializable Python dictionary.

    This serializer is the bridge between the Python backend's internal state
    and the client-side frontend application. It ensures that the complex
    object graph is converted into a clean, flat data structure suitable for
    transmission over HTTP.
    """
    def serialize(self, view_state: ViewState) -> Dict[str, Any]:
        """
        The primary method. Takes a ViewState object and returns a dictionary
        that is directly serializable to a JSON string.
        """
        return {
            "nodes": [self._serialize_node(n) for n in view_state.nodes],
            "edges": [self._serialize_edge(e) for e in view_state.edges],
        }

    def _serialize_node(self, node_data: Dict) -> Dict:
        """Ensures all values within the node dictionary are JSON-compliant."""
        # In this implementation, node data is already serializable
        return node_data

    def _serialize_edge(self, edge_data: Dict) -> Dict:
        """
        Ensures all values within the edge dictionary are JSON-compliant,
        specifically converting enums to strings.
        """
        serialized = edge_data.copy()
        # The relationship_type is an Enum member; convert it to its string value
        serialized['relationship_type'] = serialized['relationship_type'].name
        return serialized