from __future__ import annotations
import weakref
from abc import ABC, abstractmethod
from typing import Optional, Dict, Iterable, List, Literal

class CodeUnit(ABC):
    """
    Abstract Base Class for any structural element within the codebase.

    This class establishes the common interface for all nodes in the composite
    hierarchy, such as packages, modules, and classifiers. It enforces the
    presence of core identification and structural properties.
    """

    def __init__(self, name: str):
        """
        Initializes the CodeUnit with a name. The parent and children are
        initialized to their default empty states.
        """
        if not isinstance(name, str) or not name:
            raise TypeError("CodeUnit name must be a non-empty string.")
        self.name: str = name
        self._parent_ref: Optional[weakref.ref[CodeUnit]] = None
        self._children: Dict[str, CodeUnit] = {}

    @property
    def parent(self) -> Optional[CodeUnit]:
        """A weak reference to the parent element in the hierarchy."""
        if self._parent_ref:
            return self._parent_ref()
        return None

    @parent.setter
    def parent(self, value: Optional[CodeUnit]):
        self._parent_ref = weakref.ref(value) if value else None

    @property
    def fqn(self) -> str:
        """
        Computes and returns the fully-qualified name of the element.
        
        This is a recursive property that traverses up the parent hierarchy.
        The root's FQN is its own name.
        """
        if self.parent:
            return f"{self.parent.fqn}.{self.name}"
        return self.name

    def add_child(self, child: CodeUnit) -> None:
        """
        Adds a CodeUnit as a child of the current node. It sets the child's
        parent reference to self.

        Raises:
            ValueError: If a child with the same name already exists.
        """
        if child.name in self._children:
            raise ValueError(f"Child with name '{child.name}' already exists.")
        child.parent = self
        self._children[child.name] = child

    def get_child(self, name: str) -> Optional[CodeUnit]:
        """
        Retrieves a child by its local name. Returns None if not found.
        """
        return self._children.get(name)

    @property
    def children(self) -> Iterable[CodeUnit]:
        """Provides read-only access to the collection of children."""
        return self._children.values()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"

class PackageUnit(CodeUnit):
    """Represents a directory containing an `__init__.py` file."""
    pass

class ModuleUnit(CodeUnit):
    """Represents a single `.py` file."""
    pass

class ClassifierUnit(CodeUnit):
    """Represents a `class` definition."""
    def __init__(self, name: str):
        super().__init__(name)
        self.base_classes: List[str] = []
        self.is_abstract: bool = False

class MemberUnit(CodeUnit):
    """Represents a method or an attribute within a class."""
    def __init__(self, name: str):
        super().__init__(name)
        self.visibility: Literal['public', 'protected', 'private'] = "public"