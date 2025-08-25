import ast
from pathlib import Path
from abc import ABC, abstractmethod

from ..metamodel.model import Metamodel
from ..metamodel.elements import PackageUnit, ModuleUnit
from ..exceptions import SourceNotFoundError
from .visitors import HierarchicalVisitor, RelationshipVisitor

class IModelBuilder(ABC):
    """
    Abstract Base Class defining the interface for a model builder.

    A model builder is responsible for taking a source code location and
    producing a complete, populated Metamodel representation of it. This
    interface decouples the rest of the application from the specific
    strategy used to build the model (e.g., AST parsing, bytecode analysis).
    """

    @abstractmethod
    def build(self, root_path: Path, project_name: str) -> Metamodel:
        """
        The primary method of the builder. It orchestrates the entire
        construction process.

        Args:
            root_path: A `pathlib.Path` object pointing to the root directory
                       of the Python project to be analyzed.
            project_name: The top-level name of the project, used to initialize
                          the Metamodel.

        Returns:
            A fully populated Metamodel instance representing the codebase
            found at root_path.

        Raises:
            SourceNotFoundError: If the root_path does not exist or is not a
                                 directory.
        """
        raise NotImplementedError

class AstModelBuilder(IModelBuilder):
    """
    A concrete model builder that constructs the Metamodel by parsing
    Python source code into Abstract Syntax Trees (ASTs).

    This builder employs a multi-pass strategy to accurately resolve the
    codebase structure:
    1.  **Hierarchy Pass**: Discovers all packages, modules, and classifiers
        to build the basic structural hierarchy and populate the FQN registry.
    2.  **Relationship Pass**: Re-scans the ASTs to identify and resolve
        relationships (e.g., inheritance, composition) now that all
        classifiers are known.
    """

    def build(self, root_path: Path, project_name: str) -> Metamodel:
        if not root_path.is_dir():
            raise SourceNotFoundError(f"Source path {root_path} is not a valid directory.")

        model = Metamodel(project_name)
        python_files = self._find_python_files(root_path)

        parsed_files = {}
        for py_file in python_files:
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                parsed_files[py_file] = tree
            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"Warning: Skipping file {py_file} due to parsing error: {e}")
                continue

        # Hierarchy Pass
        hierarchy_visitor = HierarchicalVisitor(model)
        for py_file, tree in parsed_files.items():
            module_unit = self._ensure_module_structure(model, py_file, root_path)
            hierarchy_visitor.visit_module(module_unit, tree)

        # Relationship Pass
        relationship_visitor = RelationshipVisitor(model)
        for py_file, tree in parsed_files.items():
            relative_module_fqn = self._path_to_fqn(py_file.relative_to(root_path))
            if relative_module_fqn:
                absolute_module_fqn = f"{project_name}.{relative_module_fqn}"
            else:
                absolute_module_fqn = project_name

            module_unit = model.get_element_by_fqn(absolute_module_fqn)
            if module_unit:
                relationship_visitor.visit_module(module_unit, tree)

        return model

    def _find_python_files(self, search_path: Path) -> list[Path]:
        """Recursively finds all .py files in a given path."""
        return list(search_path.rglob("*.py"))

    def _path_to_fqn(self, relative_path: Path) -> str:
        """Converts a file path relative to the project root to an FQN."""
        # e.g., my_app/services/user.py -> my_app.services.user
        parts = list(relative_path.parts)
        if parts[-1] == "__init__.py":
            parts.pop()
        else:
            parts[-1] = parts[-1].replace(".py", "")
        return ".".join(parts)

    def _ensure_module_structure(self, model: Metamodel, file_path: Path, root_path: Path) -> ModuleUnit:
        """
        Ensures that the PackageUnit and ModuleUnit hierarchy for a given file
        path exists in the model, creating it if necessary.
        """
        relative_path = file_path.relative_to(root_path)
        current_parent = model.root_package
        
        # Ensure all intermediate packages exist
        for part in relative_path.parts[:-1]:
            child = current_parent.get_child(part)
            if child is None:
                new_package = PackageUnit(part)
                current_parent.add_child(new_package)
                model.register_element(new_package)
                current_parent = new_package
            else:
                current_parent = child

        # Ensure the module exists
        module_name = relative_path.stem if relative_path.name != "__init__.py" else None
        if module_name:
            module_unit = current_parent.get_child(module_name)
            if not module_unit:
                module_unit = ModuleUnit(module_name)
                current_parent.add_child(module_unit)
                model.register_element(module_unit)
            return module_unit
        
        # If it's an __init__.py, the module context is the package itself
        return current_parent