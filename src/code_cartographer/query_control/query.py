from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True)
class Query:
    """
    An immutable data object representing a request for a specific subgraph
    of the Metamodel.

    This object fully specifies what to show (root elements), how far to explore
    (depth), and how to prune the results (filters). It is passed to the
    AnalysisFacade's `execute_query` method.
    """
    root_fqns: List[str] = field(default_factory=list)
    depth: int = 1
    filter_rules: List[Dict[str, Any]] = field(default_factory=list)