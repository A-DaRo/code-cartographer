import pytest
from code_cartographer.query_control.query import Query
from code_cartographer.query_control.commands import (
    ICommand,
    FocusOnNodeCommand,
    ChangeDepthCommand,
    AddFilterCommand,
)
from code_cartographer.metamodel.relationship import RelationshipType

@pytest.fixture
def initial_query() -> Query:
    """Provides a default Query object for testing transformations."""
    return Query(
        root_fqns=["a.b.Initial"],
        depth=2,
        filter_rules=[{'type': 'relationship', 'exclude_types': [RelationshipType.DEPENDENCY]}]
    )

def test_focus_on_node_command(initial_query: Query):
    """Tests that FocusOnNodeCommand correctly resets the root FQN and depth."""
    command = FocusOnNodeCommand(new_root_fqn="x.y.NewFocus")
    new_query = command.execute(initial_query)

    assert new_query.root_fqns == ["x.y.NewFocus"]
    assert new_query.depth == 2 # A default depth could be set, here we assume it copies
    assert new_query.filter_rules == initial_query.filter_rules # Filters are preserved

def test_change_depth_command(initial_query: Query):
    """Tests that ChangeDepthCommand updates only the depth."""
    command = ChangeDepthCommand(new_depth=5)
    new_query = command.execute(initial_query)

    assert new_query.root_fqns == initial_query.root_fqns
    assert new_query.depth == 5
    assert new_query.filter_rules == initial_query.filter_rules

def test_add_filter_command(initial_query: Query):
    """Tests that AddFilterCommand correctly appends a new filter rule."""
    new_filter = {'type': 'node', 'exclude_names': ["*Impl"]}
    command = AddFilterCommand(new_filter=new_filter)
    new_query = command.execute(initial_query)
    
    assert new_query.root_fqns == initial_query.root_fqns
    assert new_query.depth == initial_query.depth
    assert len(new_query.filter_rules) == 2
    assert new_query.filter_rules[0] == initial_query.filter_rules[0]
    assert new_query.filter_rules[1] == new_filter

def test_commands_are_immutable(initial_query: Query):
    """Ensures that executing a command does not modify the original query."""
    original_fqns = list(initial_query.root_fqns)
    command = FocusOnNodeCommand("new.node")
    command.execute(initial_query)

    assert initial_query.root_fqns == original_fqns