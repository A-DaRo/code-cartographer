from dataclasses import is_dataclass
from code_cartographer.query_control.query import Query
from code_cartographer.query_control.view_state import ViewState

def test_query_is_immutable_dataclass():
    """Tests that the Query class is a frozen dataclass."""
    assert is_dataclass(Query)
    assert Query.__dataclass_params__.frozen is True

def test_view_state_is_dataclass():
    """Tests that the ViewState class is a standard (mutable) dataclass."""
    assert is_dataclass(ViewState)
    assert ViewState.__dataclass_params__.frozen is False # It's a DTO, can be modified