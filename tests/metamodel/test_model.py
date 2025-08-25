import pytest
from code_cartographer.metamodel.model import Metamodel
from code_cartographer.metamodel.elements import PackageUnit, ModuleUnit, ClassifierUnit
from code_cartographer.metamodel.relationship import Relationship, RelationshipType

@pytest.fixture
def empty_metamodel():
    """A fixture that provides an empty Metamodel instance."""
    return Metamodel("test_project")

@pytest.fixture
def populated_metamodel():
    """A fixture that provides a Metamodel with a few registered elements."""
    model = Metamodel("my_app")
    
    # Create and register elements
    root = model.root_package
    api = PackageUnit("api")
    models = ModuleUnit("models")
    user_class = ClassifierUnit("User")
    
    root.add_child(api)
    model.register_element(api)
    
    api.add_child(models)
    model.register_element(models)
    
    models.add_child(user_class)
    model.register_element(user_class)
    
    # Create and register relationships
    rel1 = Relationship("my_app.api.models.User", "builtins.object", RelationshipType.INHERITANCE)
    rel2 = Relationship("my_app.api.handlers.UserHandler", "my_app.api.models.User", RelationshipType.DEPENDENCY) # outgoing from UserHandler
    rel3 = Relationship("my_app.api.models.User", "my_app.api.models.Profile", RelationshipType.COMPOSITION) # incoming to Profile
    
    model.register_relationship(rel1)
    model.register_relationship(rel2)
    model.register_relationship(rel3)
    
    return model

def test_metamodel_initialization(empty_metamodel: Metamodel):
    """Tests that the Metamodel is initialized correctly."""
    assert empty_metamodel.root_package.name == "test_project"
    assert empty_metamodel.root_package.fqn == "test_project"
    assert empty_metamodel.get_element_by_fqn("test_project") is not None

def test_register_element(empty_metamodel: Metamodel):
    """Tests registration and retrieval of a CodeUnit."""
    module = ModuleUnit("my_module")
    empty_metamodel.root_package.add_child(module)
    empty_metamodel.register_element(module)
    
    assert empty_metamodel.get_element_by_fqn("test_project.my_module") is module

def test_register_element_raises_on_duplicate_fqn(empty_metamodel: Metamodel):
    """Tests that registering an element with a duplicate FQN raises a KeyError."""
    module1 = ModuleUnit("my_module")
    module2_same_fqn = ModuleUnit("my_module")
    
    empty_metamodel.root_package.add_child(module1)
    empty_metamodel.register_element(module1)

    empty_metamodel.root_package.add_child(module2_same_fqn)
    
    with pytest.raises(KeyError, match="Element with FQN 'test_project.my_module' is already registered."):
        empty_metamodel.register_element(module2_same_fqn)

def test_get_relationships_for_fqn(populated_metamodel: Metamodel):
    """Tests the relationship query method."""
    user_fqn = "my_app.api.models.User"
    
    # Test direction: both (default)
    rels_both = populated_metamodel.get_relationships_for_fqn(user_fqn)
    assert len(rels_both) == 3
    
    # Test direction: outgoing
    rels_outgoing = populated_metamodel.get_relationships_for_fqn(user_fqn, direction='outgoing')
    assert len(rels_outgoing) == 2
    assert all(r.source_fqn == user_fqn for r in rels_outgoing)
    
    # Test direction: incoming
    rels_incoming = populated_metamodel.get_relationships_for_fqn(user_fqn, direction='incoming')
    assert len(rels_incoming) == 1
    assert all(r.target_fqn == user_fqn for r in rels_incoming)

def test_get_relationships_for_fqn_no_match():
    """Tests that an empty list is returned for an FQN with no relationships."""
    model = Metamodel("empty_project")
    rels = model.get_relationships_for_fqn("non.existent.fqn")
    assert rels == []