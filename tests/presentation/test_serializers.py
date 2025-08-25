from code_cartographer.query_control.view_state import ViewState
from code_cartographer.presentation.serializers import JsonSerializer
from code_cartographer.metamodel.relationship import RelationshipType

def test_json_serializer_converts_enum_to_string():
    """
    Tests that the JsonSerializer correctly transforms enum members into
    simple strings for JSON compatibility.
    """
    # GIVEN a ViewState containing an edge with an enum type
    view_state = ViewState(
        nodes=[{'fqn': 'a.B', 'name': 'B', 'element_type': 'class'}],
        edges=[{
            'source_fqn': 'a.A',
            'target_fqn': 'a.B',
            'relationship_type': RelationshipType.COMPOSITION # This is an enum member
        }]
    )
    serializer = JsonSerializer()

    # WHEN the view state is serialized
    result = serializer.serialize(view_state)

    # THEN the relationship_type in the output dict should be a string
    assert isinstance(result, dict)
    assert "edges" in result
    assert len(result["edges"]) == 1
    edge = result["edges"][0]
    assert edge["relationship_type"] == "COMPOSITION" # The string name of the enum member