from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import replace

from .query import Query

class ICommand(ABC):
    """
    Defines the interface for a command that modifies the application's
    query state.
    """
    @abstractmethod
    def execute(self, current_query: Query) -> Query:
        """
        Takes the current Query state and returns a new Query object
        reflecting the action of the command. Commands must be immutable and not
        modify the current_query in place.

        Args:
            current_query: The query state before the command is executed.

        Returns:
            A new Query object representing the updated state.
        """
        raise NotImplementedError

class FocusOnNodeCommand(ICommand):
    """A command to change the root of the query and reset the view."""
    def __init__(self, new_root_fqn: str):
        self._new_root_fqn = new_root_fqn

    def execute(self, current_query: Query) -> Query:
        return replace(current_query, root_fqns=[self._new_root_fqn])

class ChangeDepthCommand(ICommand):
    """A command to change the traversal depth of the query."""
    def __init__(self, new_depth: int):
        self._new_depth = new_depth

    def execute(self, current_query: Query) -> Query:
        return replace(current_query, depth=self._new_depth)

class AddFilterCommand(ICommand):
    """A command to add a new filter rule to the query."""
    def __init__(self, new_filter: Dict[str, Any]):
        self._new_filter = new_filter

    def execute(self, current_query: Query) -> Query:
        # Create a new list to maintain immutability
        new_filters = list(current_query.filter_rules)
        new_filters.append(self._new_filter)
        return replace(current_query, filter_rules=new_filters)