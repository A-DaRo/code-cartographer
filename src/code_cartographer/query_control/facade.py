from __future__ import annotations
from pathlib import Path
from collections import deque
from typing import Optional, Set

from ..metamodel.model import Metamodel
from ..metamodel.elements import CodeUnit, ClassifierUnit, PackageUnit, ModuleUnit
from ..metamodel.relationship import Relationship
from ..construction.builders import IModelBuilder
from ..exceptions import SourceNotFoundError, ModelStateError
from .query import Query
from .view_state import ViewState

class AnalysisFacade:
    """
    Provides a simplified, unified interface to the Code Cartographer's core
    functionality.

    The AnalysisFacade is the primary entry point for any client (e.g., a CLI,
    GUI, or web server). It encapsulates the workflow of loading a project,
    managing the state of the Metamodel, and executing queries against it to
    generate specific views of the codebase. This class hides the internal
    complexity of model construction and graph traversal from the client.
    """
    def __init__(self, builder: IModelBuilder):
        """
        Initializes the facade. It requires a concrete IModelBuilder instance
        to be injected, decoupling the facade from any specific construction
        strategy (like AstModelBuilder).

        Args:
            builder: A concrete implementation of the IModelBuilder interface.
        """
        self._model: Optional[Metamodel] = None
        self._builder: IModelBuilder = builder

    def load_project(self, root_path: Path, project_name: str) -> None:
        """
        Orchestrates the loading of a new project. It uses the injected builder
        to construct a new Metamodel and stores it internally, replacing any
        previously loaded model.

        Raises:
            SourceNotFoundError: Propagated from the builder if the path is invalid.
        """
        new_model = self._builder.build(root_path, project_name)
        self._model = new_model

    def execute_query(self, query: Query) -> ViewState:
        """
        The core method of the facade. It takes a Query object specifying the
        desired view and returns a ViewState Data Transfer Object (DTO)
        containing the results. The method is responsible for traversing the
        Metamodel graph according to the query's parameters.
        """
        if self._model is None:
            raise ModelStateError("No project is loaded.")

        nodes_to_render: dict[str, dict] = {}
        edges_to_render: set[tuple] = set()
        
        queue = deque([(fqn, 0) for fqn in query.root_fqns])
        visited_fqns = set(query.root_fqns)

        while queue:
            current_fqn, current_depth = queue.popleft()
            
            element = self._model.get_element_by_fqn(current_fqn)
            if not element:
                continue
            
            nodes_to_render[current_fqn] = self._serialize_element(element)

            if current_depth >= query.depth:
                continue

            relationships = self._model.get_relationships_for_fqn(current_fqn, direction='both')

            for rel in relationships:
                if self._is_relationship_filtered(rel, query):
                    continue
                
                # Determine the 'other' side of the relationship
                if rel.source_fqn == current_fqn:
                    target_fqn = rel.target_fqn
                else:
                    target_fqn = rel.source_fqn
                
                # Ensure the edge is always represented in a canonical direction
                # to avoid duplicates in the set
                edge_tuple = tuple(sorted((rel.source_fqn, rel.target_fqn))) + (rel.type.name,)
                edges_to_render.add(edge_tuple)

                if target_fqn not in visited_fqns:
                    visited_fqns.add(target_fqn)
                    queue.append((target_fqn, current_depth + 1))
        
        # Add all nodes that are part of the rendered edges
        for source, target, _ in edges_to_render:
            if source not in nodes_to_render:
                element = self._model.get_element_by_fqn(source)
                if element: nodes_to_render[source] = self._serialize_element(element)
            if target not in nodes_to_render:
                element = self._model.get_element_by_fqn(target)
                if element: nodes_to_render[target] = self._serialize_element(element)

        # Create final lists for the ViewState
        final_nodes = list(nodes_to_render.values())
        final_edges = [{
            'source_fqn': source,
            'target_fqn': target,
            'relationship_type': rel_type_name,
        } for source, target, rel_type_name in edges_to_render]
        
        return ViewState(nodes=final_nodes, edges=final_edges)

    def _serialize_element(self, element: CodeUnit) -> dict:
        """Converts a CodeUnit object to a serializable dictionary."""
        element_type = "unknown"
        if isinstance(element, ClassifierUnit):
            element_type = "class"
        elif isinstance(element, ModuleUnit):
            element_type = "module"
        elif isinstance(element, PackageUnit):
            element_type = "package"
            
        return {
            'fqn': element.fqn,
            'name': element.name,
            'element_type': element_type,
            'parent_fqn': element.parent.fqn if element.parent else None,
        }

    def _is_relationship_filtered(self, rel: Relationship, query: Query) -> bool:
        """Checks if a relationship should be filtered based on query rules."""
        for rule in query.filter_rules:
            if 'exclude_types' in rule and rel.type in rule['exclude_types']:
                return True
        return False