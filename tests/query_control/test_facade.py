import pytest
from pathlib import Path
from unittest.mock import MagicMock, create_autospec

from code_cartographer.construction.builders import IModelBuilder
from code_cartographer.metamodel.model import Metamodel
from code_cartographer.metamodel.elements import ClassifierUnit, PackageUnit
from code_cartographer.metamodel.relationship import Relationship, RelationshipType
from code_cartographer.query_control.facade import AnalysisFacade
from code_cartographer.query_control.query import Query
from code_cartographer.exceptions import ModelStateError

@pytest.fixture
def mock_builder() -> MagicMock:
    """Provides a mock IModelBuilder."""
    return create_autospec(IModelBuilder)

@pytest.fixture
def populated_model() -> Metamodel:
    """Provides a consistent, pre-populated Metamodel for query testing."""
    model = Metamodel("my_project")
    root = model.root_package
    
    # Elements
    A = ClassifierUnit("A")
    B = ClassifierUnit("B")
    C = ClassifierUnit("C")
    D = ClassifierUnit("D") # Unconnected
    root.add_child(A)
    root.add_child(B)
    root.add_child(C)
    root.add_child(D)
    model.register_element(A)
    model.register_element(B)
    model.register_element(C)
    model.register_element(D)
    
    # Relationships
    model.register_relationship(Relationship("my_project.A", "my_project.B", RelationshipType.ASSOCIATION))
    model.register_relationship(Relationship("my_project.B", "my_project.C", RelationshipType.DEPENDENCY))
    
    return model

@pytest.fixture
def loaded_facade(mock_builder: MagicMock, populated_model: Metamodel) -> AnalysisFacade:
    """Provides a facade that has already 'loaded' the populated_model."""
    mock_builder.build.return_value = populated_model
    facade = AnalysisFacade(mock_builder)
    facade.load_project(Path("/fake/path"), "my_project")
    return facade

def test_facade_init(mock_builder: MagicMock):
    """Tests that the facade initializes correctly."""
    facade = AnalysisFacade(mock_builder)
    assert facade._builder is mock_builder
    assert facade._model is None

def test_load_project(mock_builder: MagicMock, populated_model: Metamodel):
    """Tests that load_project uses the builder and sets the internal model."""
    mock_builder.build.return_value = populated_model
    facade = AnalysisFacade(mock_builder)
    
    fake_path = Path("/fake/path")
    facade.load_project(fake_path, "my_project")
    
    mock_builder.build.assert_called_once_with(fake_path, "my_project")
    assert facade._model is populated_model

def test_execute_query_raises_if_not_loaded(mock_builder: MagicMock):
    """Tests that a query fails if no project has been loaded."""
    facade = AnalysisFacade(mock_builder)
    query = Query(root_fqns=[], depth=0)
    with pytest.raises(ModelStateError, match="No project is loaded."):
        facade.execute_query(query)

def test_query_depth_0(loaded_facade: AnalysisFacade):
    """Tests that a query with depth=0 returns only the root node."""
    query = Query(root_fqns=["my_project.A"], depth=0)
    view_state = loaded_facade.execute_query(query)
    
    assert len(view_state.nodes) == 1
    assert view_state.nodes[0]['fqn'] == "my_project.A"
    assert len(view_state.edges) == 0

def test_query_depth_1(loaded_facade: AnalysisFacade):
    """Tests a query with depth=1, showing direct neighbors."""
    query = Query(root_fqns=["my_project.A"], depth=1)
    view_state = loaded_facade.execute_query(query)
    
    node_fqns = {n['fqn'] for n in view_state.nodes}
    assert node_fqns == {"my_project.A", "my_project.B"}
    assert len(view_state.edges) == 1
    edge = view_state.edges[0]
    assert edge['source_fqn'] == "my_project.A"
    assert edge['target_fqn'] == "my_project.B"

def test_query_depth_2(loaded_facade: AnalysisFacade):
    """Tests a query that traverses multiple steps."""
    query = Query(root_fqns=["my_project.A"], depth=2)
    view_state = loaded_facade.execute_query(query)
    
    node_fqns = {n['fqn'] for n in view_state.nodes}
    assert node_fqns == {"my_project.A", "my_project.B", "my_project.C"}
    assert len(view_state.edges) == 2

def test_query_respects_depth_limit(loaded_facade: AnalysisFacade):
    """Ensures traversal stops at the specified depth."""
    query = Query(root_fqns=["my_project.A"], depth=1)
    view_state = loaded_facade.execute_query(query)

    node_fqns = {n['fqn'] for n in view_state.nodes}
    assert "my_project.C" not in node_fqns

def test_query_with_relationship_filter(loaded_facade: AnalysisFacade):
    """Tests that a filter can exclude certain relationship types."""
    # This filter should exclude the B -> C edge
    filter_rule = {'exclude_types': [RelationshipType.DEPENDENCY]}
    query = Query(root_fqns=["my_project.A"], depth=5, filter_rules=[filter_rule])
    view_state = loaded_facade.execute_query(query)
    
    node_fqns = {n['fqn'] for n in view_state.nodes}
    # C should not be present because the edge leading to it was filtered
    assert node_fqns == {"my_project.A", "my_project.B"}
    assert len(view_state.edges) == 1
    assert view_state.edges[0]['relationship_type'] == "ASSOCIATION"