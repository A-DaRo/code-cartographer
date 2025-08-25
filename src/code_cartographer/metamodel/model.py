from __future__ import annotations
from typing import Optional, Dict, List, Literal

from .elements import CodeUnit, PackageUnit
from .relationship import Relationship

class Metamodel:
    """
    The root container for the entire codebase representation.

    This class holds the hierarchical structure of the code, starting from the
    root package, and maintains indexed registries for all code elements and
    relationships. This allows for efficient O(1) lookups of any element by its
    fully-qualified name and fast querying of relationships.
    """
    def __init__(self, project_name: str):
        """
        Initializes the Metamodel. It creates the root PackageUnit with the
        given project_name and registers it.
        """
        self.root_package: PackageUnit = PackageUnit(project_name)
        self._fqn_registry: Dict[str, CodeUnit] = {}
        self._relationship_registry: List[Relationship] = []
        
        # The root package must also be registered
        self.register_element(self.root_package)

    def register_element(self, element: CodeUnit) -> None:
        """
        Registers a CodeUnit in the FQN registry.

        This method should be called by the construction layer every time a
        new element is added to the hierarchy.

        Raises:
            KeyError: If an element with the same FQN is already registered.
        """
        fqn = element.fqn
        if fqn in self._fqn_registry:
            raise KeyError(f"Element with FQN '{fqn}' is already registered.")
        self._fqn_registry[fqn] = element

    def register_relationship(self, relationship: Relationship) -> None:
        """Adds a Relationship to the relationship registry."""
        self._relationship_registry.append(relationship)

    def get_element_by_fqn(self, fqn: str) -> Optional[CodeUnit]:
        """
        Retrieves a CodeUnit from the FQN registry in O(1) time.

        Returns:
            The CodeUnit if found, otherwise None.
        """
        return self._fqn_registry.get(fqn)

    def get_relationships_for_fqn(
        self,
        fqn: str,
        direction: Literal['outgoing', 'incoming', 'both'] = 'both'
    ) -> List[Relationship]:
        """
        Scans the relationship registry and returns a list of all relationships
        connected to the given FQN.
        
        The `direction` parameter filters for relationships where the FQN is
        the source, target, or either.
        """
        results = []
        is_outgoing = direction in ('outgoing', 'both')
        is_incoming = direction in ('incoming', 'both')
        
        for rel in self._relationship_registry:
            if is_outgoing and rel.source_fqn == fqn:
                results.append(rel)
            elif is_incoming and rel.target_fqn == fqn:
                results.append(rel)
        return results