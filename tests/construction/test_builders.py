import pytest
from pathlib import Path

from code_cartographer.construction.builders import AstModelBuilder
from code_cartographer.exceptions import SourceNotFoundError
from code_cartographer.metamodel.relationship import RelationshipType

def test_builder_raises_on_invalid_path():
    """Tests that the builder raises SourceNotFoundError for a non-existent directory."""
    builder = AstModelBuilder()
    invalid_path = Path("/non/existent/path")
    with pytest.raises(SourceNotFoundError, match=f"Source path {invalid_path} is not a valid directory."):
        builder.build(invalid_path, "test")

def test_builder_integration_builds_full_model(sample_project: Path):
    """
    An integration test to ensure the builder correctly constructs the
    full Metamodel from the sample project source.
    """
    # GIVEN an AST Model Builder
    builder = AstModelBuilder()
    
    # WHEN the model is built from the sample project path
    model = builder.build(sample_project, "my_app")
    
    # THEN the hierarchy should be correct
    assert model.root_package.name == "my_app"
    
    # Check for correct package/module structure
    app_root = model.get_element_by_fqn("my_app")
    assert app_root is not None
    
    models_pkg = model.get_element_by_fqn("my_app.models")
    assert models_pkg is not None
    assert models_pkg.parent.fqn == "my_app"

    user_module = model.get_element_by_fqn("my_app.models.user")
    assert user_module is not None
    
    # Check for correct classifiers
    user_class = model.get_element_by_fqn("my_app.models.user.User")
    assert user_class is not None
    assert user_class.parent.fqn == "my_app.models.user"
    
    app_class = model.get_element_by_fqn("my_app.app.Application")
    assert app_class is not None
    
    # THEN inheritance relationships should be correctly identified
    inheritance_rels = [
        r for r in model._relationship_registry 
        if r.type == RelationshipType.INHERITANCE
    ]
    assert len(inheritance_rels) == 1
    user_inheritance = inheritance_rels[0]
    assert user_inheritance.source_fqn == "my_app.models.user.User"
    assert user_inheritance.target_fqn == "my_app.models.base.ModelBase"
    
    # THEN composition relationships should be correctly identified
    composition_rels = [
        r for r in model._relationship_registry
        if r.type == RelationshipType.COMPOSITION
    ]
    assert len(composition_rels) == 2
    
    # Check for self.repo = UserRepository()
    repo_composition = next(r for r in composition_rels if r.source_fqn == "my_app.app.Application" and r.target_fqn == "my_app.services.repository.UserRepository")
    assert repo_composition is not None

    # Check for self.user_model = user.User()
    user_composition = next(r for r in composition_rels if r.source_fqn == "my_app.app.Application" and r.target_fqn == "my_app.models.user.User")
    assert user_composition is not None