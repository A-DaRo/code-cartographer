from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any

class RelationshipType(str, Enum):
    """An enumeration for the different kinds of relationships."""
    INHERITANCE = "INHERITANCE"
    COMPOSITION = "COMPOSITION"
    AGGREGATION = "AGGREGATION"
    ASSOCIATION = "ASSOCIATION"
    DEPENDENCY = "DEPENDENCY"

@dataclass(frozen=True)
class Relationship:
    """
    Represents a single, directed relationship between two classifiers.

    This is an immutable data structure that captures the source, target, type,
    and other metadata of a relationship. By treating relationships as
    first-class objects, we enable complex queries and analysis of the
    codebase's coupling and structure.
    """
    source_fqn: str
    target_fqn: str
    type: RelationshipType
    metadata: Dict[str, Any] = field(default_factory=dict)