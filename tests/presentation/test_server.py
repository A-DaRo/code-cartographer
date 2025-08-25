import pytest
from unittest.mock import MagicMock, create_autospec

from fastapi.testclient import TestClient

from code_cartographer.query_control.facade import AnalysisFacade
from code_cartographer.query_control.view_state import ViewState
from code_cartographer.query_control.query import Query
from code_cartographer.presentation.server import APIServer
from code_cartographer.construction.builders import IModelBuilder
from code_cartographer.metamodel.relationship import RelationshipType

@pytest.fixture
def mock_facade() -> MagicMock:
    """Provides a mock AnalysisFacade with a pre-configured `execute_query` method."""
    facade = create_autospec(AnalysisFacade)
    
    # Configure the mock to return a specific ViewState when called
    sample_view_state = ViewState(
        nodes=[{'fqn': 'test.A', 'name': 'A', 'element_type': 'class'}],
        edges=[{
            'source_fqn': 'test.A',
            'target_fqn': 'test.B',
            'relationship_type': RelationshipType.INHERITANCE,
        }]
    )
    facade.execute_query.return_value = sample_view_state
    
    return facade

@pytest.fixture
def api_client(mock_facade: MagicMock) -> TestClient:
    """Provides a FastAPI TestClient configured with a mock facade."""
    server = APIServer(facade=mock_facade)
    return TestClient(server.app)

def test_get_status_endpoint(api_client: TestClient):
    """Tests the /api/v1/status health check endpoint."""
    response = api_client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "project_loaded": False} # No project loaded yet

def test_handle_query_endpoint(api_client: TestClient, mock_facade: MagicMock):
    """Tests a successful POST request to the /api/v1/query endpoint."""
    # GIVEN a query dictionary to be sent as the JSON body
    query_dict = {
        "root_fqns": ["test.A"],
        "depth": 1,
        "filter_rules": []
    }

    # WHEN a POST request is made to the query endpoint
    response = api_client.post("/api/v1/query", json=query_dict)

    # THEN the response should be successful and contain the serialized view state
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['nodes'][0]['fqn'] == 'test.A'
    assert response_data['edges'][0]['relationship_type'] == 'INHERITANCE' # Serialized to string

    # AND the facade's execute_query method should have been called with the correct Query object
    mock_facade.execute_query.assert_called_once()
    call_args = mock_facade.execute_query.call_args[0]
    assert len(call_args) == 1
    query_arg = call_args[0]
    assert isinstance(query_arg, Query)
    assert query_arg.root_fqns == ["test.A"]
    assert query_arg.depth == 1

def test_handle_query_with_bad_request(api_client: TestClient):
    """Tests that the API returns a 422 Unprocessable Entity for an invalid query body."""
    # GIVEN a query with a field of the wrong type
    bad_query_dict = {
        "root_fqns": ["test.A"],
        "depth": "not-an-integer", # Invalid type
        "filter_rules": []
    }
    
    # WHEN the request is made
    response = api_client.post("/api/v1/query", json=bad_query_dict)
    
    # THEN the response should indicate a validation error
    assert response.status_code == 422