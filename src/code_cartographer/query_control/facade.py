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
        
        The traversal algorithm explores two types of connections:
        1. Structural Children: Navigating from a package to its modules/sub-packages,
           or a module to its classes. This does not increase the traversal depth.
        2. Relational Edges: Following relationships like inheritance or composition.
           This *does* increase the traversal depth.
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
            
            # Add the current element to the results.
            nodes_to_render[current_fqn] = self._serialize_element(element)

            # --- Structural Traversal ---
            # If the element is a container (package/module), add its children to the queue.
            # This traversal does NOT increase depth.
            if isinstance(element, (PackageUnit, ModuleUnit)):
                for child in element.children:
                    if child.fqn not in visited_fqns:
                        visited_fqns.add(child.fqn)
                        queue.append((child.fqn, current_depth))

            # --- Relational Traversal ---
            # If we are at the depth limit, we stop exploring further relationships.
            if current_depth >= query.depth:
                continue

            relationships = self._model.get_relationships_for_fqn(current_fqn, direction='both')
            for rel in relationships:
                if self._is_relationship_filtered(rel, query):
                    continue
                
                edge_tuple = (rel.source_fqn, rel.target_fqn, rel.type.name)
                edges_to_render.add(edge_tuple)

                # Determine the "other" side of the relationship to continue the traversal.
                node_to_visit_next = rel.target_fqn if rel.source_fqn == current_fqn else rel.source_fqn
                
                if node_to_visit_next not in visited_fqns:
                    visited_fqns.add(node_to_visit_next)
                    # This traversal *does* increase depth.
                    queue.append((node_to_visit_next, current_depth + 1))
        
        # After traversal, ensure all nodes that are part of an edge are in the final node list.
        all_edge_fqns = {fqn for edge in edges_to_render for fqn in edge[:2]}
        for fqn in all_edge_fqns:
            if fqn not in nodes_to_render:
                element = self._model.get_element_by_fqn(fqn)
                if element:
                    nodes_to_render[fqn] = self._serialize_element(element)

        # Create final lists for the ViewState.
        final_nodes = list(nodes_to_render.values())
        final_edges = [{
            'source_fqn': source,
            'target_fqn': target,
            'relationship_type': rel_type_name,
        } for source, target, rel_type_name in edges_to_render]
        
        return ViewState(nodes=final_nodes, edges=final_edges, root_fqns=query.root_fqns)

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