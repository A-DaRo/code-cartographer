import ast
from pathlib import Path

from ..metamodel.model import Metamodel
from ..metamodel.elements import ModuleUnit, ClassifierUnit
from ..metamodel.relationship import Relationship, RelationshipType

class HierarchicalVisitor(ast.NodeVisitor):
    """
    An AST visitor for the first construction pass (Hierarchy Pass).

    This visitor's only responsibility is to traverse an AST and identify
    the namespace hierarchy: classifiers. It populates
    a Metamodel instance with these structural elements but does *not* attempt
    to resolve relationships between them.
    """

    def __init__(self, model: Metamodel):
        """Initializes the visitor with a reference to the Metamodel."""
        self._model = model
        self._current_module: ModuleUnit = None

    def visit_module(self, module_unit: ModuleUnit, tree: ast.Module):
        """
        A custom entry point to set the context for a file traversal.
        Sets the current module and then visits the AST tree.
        """
        self._current_module = module_unit
        self.visit(tree)

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Called for each `class ...:` statement. Creates and registers
        a ClassifierUnit in the Metamodel.
        """
        classifier = ClassifierUnit(name=node.name)
        self._current_module.add_child(classifier)
        self._model.register_element(classifier)
        
        # Store base class names as strings for later resolution
        for base in node.bases:
            if isinstance(base, ast.Name):
                classifier.base_classes.append(base.id)
            elif isinstance(base, ast.Attribute): # e.g., inherits from something.Something
                # This is a simplification; a full implementation would reconstruct the name
                # For now, we capture the final part. The relationship visitor will resolve it.
                classifier.base_classes.append(base.attr)

        self.generic_visit(node) # Visit nested classes

class RelationshipVisitor(ast.NodeVisitor):
    """
    An AST visitor for the second construction pass (Relationship Pass).

    This visitor traverses an AST with the assumption that the Metamodel's
    FQN registry is already fully populated with all classifiers. Its purpose
    is to identify, resolve, and register relationships like inheritance and
    composition.
    """
    def __init__(self, model: Metamodel):
        self._model = model
        self._current_module: ModuleUnit = None
        self._current_classifier: ClassifierUnit = None
        self._imports: dict[str, str] = {}

    def visit_module(self, module_unit: ModuleUnit, tree: ast.Module):
        """Sets the context for a file traversal and resets local state."""
        self._current_module = module_unit
        self._imports = {}
        self._current_classifier = None
        self.visit(tree)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        base_module = ""
        if node.level > 0: # Relative import
            path_parts = self._current_module.fqn.split('.')
            base_module = ".".join(path_parts[:-(node.level -1)])
        if node.module:
            base_module = f"{base_module}.{node.module}" if base_module else node.module
            
        for alias in node.names:
            self._imports[alias.asname or alias.name] = f"{base_module}.{alias.name}"
        self.generic_visit(node)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Identifies inheritance relationships."""
        classifier_fqn = f"{self._current_module.fqn}.{node.name}"
        classifier = self._model.get_element_by_fqn(classifier_fqn)
        
        if not classifier:
            return # Should not happen if hierarchy pass was correct

        self._current_classifier = classifier
        
        # Inheritance
        for base_name in classifier.base_classes:
            resolved_fqn = self._resolve_name_to_fqn(base_name)
            if resolved_fqn and self._model.get_element_by_fqn(resolved_fqn):
                rel = Relationship(
                    source_fqn=classifier.fqn,
                    target_fqn=resolved_fqn,
                    type=RelationshipType.INHERITANCE
                )
                self._model.register_relationship(rel)

        self.generic_visit(node)
        self._current_classifier = None

    def visit_Assign(self, node: ast.Assign):
        """Identifies composition relationships via instance attribute assignment."""
        if not self._current_classifier:
            self.generic_visit(node)
            return

        # Looking for `self.foo = Bar()`
        if isinstance(node.value, ast.Call) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Attribute) and \
               isinstance(target.value, ast.Name) and target.value.id == 'self':
                
                # Get the name of the class being instantiated
                class_name_node = node.value.func
                class_name = ""
                if isinstance(class_name_node, ast.Name):
                    class_name = class_name_node.id
                elif isinstance(class_name_node, ast.Attribute): # e.g., something.Bar()
                    # A more robust solution would trace the full attribute chain
                    class_name = self._reconstruct_attribute_name(class_name_node)
                
                if class_name:
                    resolved_fqn = self._resolve_name_to_fqn(class_name)
                    if resolved_fqn and self._model.get_element_by_fqn(resolved_fqn):
                        rel = Relationship(
                            source_fqn=self._current_classifier.fqn,
                            target_fqn=resolved_fqn,
                            type=RelationshipType.COMPOSITION
                        )
                        self._model.register_relationship(rel)
        
        self.generic_visit(node)

    def _reconstruct_attribute_name(self, node: ast.Attribute) -> str:
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
            return ".".join(reversed(parts))
        return "" # Could not fully reconstruct

    def _resolve_name_to_fqn(self, name: str) -> str | None:
        """Attempts to resolve a local name to a full FQN using imports."""
        if name in self._imports:
            return self._imports[name]
        
        # Handle cases like `models.User` where `models` is an imported module
        if "." in name:
            base, *rest = name.split('.')
            if base in self._imports:
                return f"{self._imports[base]}.{'.'.join(rest)}"

        # Assume it's a name in the current module
        potential_fqn = f"{self._current_module.fqn}.{name}"
        if self._model.get_element_by_fqn(potential_fqn):
            return potential_fqn
            
        return None # Could not resolve