import sys
from io import StringIO
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from code_cartographer.query_control.view_state import ViewState
from code_cartographer.presentation.renderers import GraphvizRenderer, TextualRenderer
from code_cartographer.exceptions import RenderingError

@pytest.fixture
def sample_view_state() -> ViewState:
    """Provides a consistent ViewState object for testing renderers."""
    return ViewState(
        nodes=[
            {'fqn': 'my_app', 'name': 'my_app', 'element_type': 'package', 'parent_fqn': None},
            {'fqn': 'my_app.Car', 'name': 'Car', 'element_type': 'class', 'parent_fqn': 'my_app'},
            {'fqn': 'my_app.Engine', 'name': 'Engine', 'element_type': 'class', 'parent_fqn': 'my_app'},
        ],
        edges=[
            {
                'source_fqn': 'my_app.Car',
                'target_fqn': 'my_app.Engine',
                'relationship_type': 'COMPOSITION'
            }
        ]
    )

# --- Tests for GraphvizRenderer ---

@patch('graphviz.Digraph')
def test_graphviz_renderer_orchestration(MockDigraph, sample_view_state: ViewState, tmp_path: Path):
    """
    Tests that the GraphvizRenderer correctly uses the graphviz library
    by mocking the Digraph object.
    """
    # GIVEN a mocked Digraph instance and a renderer
    mock_dot_instance = MockDigraph.return_value
    renderer = GraphvizRenderer()
    output_path = tmp_path / "diagram.svg"

    # WHEN rendering the view state
    renderer.render(sample_view_state, output_path)

    # THEN the Digraph should be initialized with correct attributes
    MockDigraph.assert_called_once()
    mock_dot_instance.attr.assert_called_with('graph', rankdir='TB', splines='ortho')

    # THEN nodes should be added with correct styles
    assert mock_dot_instance.node.call_count == 3
    mock_dot_instance.node.assert_any_call(
        name='my_app',
        label='<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD BGCOLOR="#E6F2FA"><B>my_app</B></TD></TR></TABLE>',
        shape='plain'
    )
    mock_dot_instance.node.assert_any_call(
        name='my_app.Car',
        label='<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD BGCOLOR="#FFFFFF"><B>Car</B></TD></TR></TABLE>',
        shape='plain'
    )

    # THEN edges should be added with correct styles
    mock_dot_instance.edge.assert_called_once_with(
        'my_app.Car',
        'my_app.Engine',
        arrowhead='diamond',
        style='dashed'
    )

    # THEN the final render call should be correct
    mock_dot_instance.render.assert_called_once_with(
        str(output_path.with_suffix('')),
        format='svg',
        view=False,
        cleanup=True
    )

@patch('graphviz.Digraph')
def test_graphviz_renderer_wraps_exception(MockDigraph, sample_view_state: ViewState, tmp_path: Path):
    """
    Tests that exceptions from the graphviz library are wrapped in RenderingError.
    """
    # GIVEN a mocked Digraph that raises an exception on render
    mock_dot_instance = MockDigraph.return_value
    mock_dot_instance.render.side_effect = Exception("Graphviz executable not found")
    renderer = GraphvizRenderer()
    output_path = tmp_path / "diagram.png"
    
    # WHEN rendering is attempted
    # THEN a RenderingError should be raised with a helpful message
    with pytest.raises(RenderingError, match="Failed to execute Graphviz."):
        renderer.render(sample_view_state, output_path)

# --- Tests for TextualRenderer ---

def test_textual_renderer_output(sample_view_state: ViewState):
    """
    Tests the textual renderer's output format for a simple hierarchy.
    """
    # GIVEN a renderer and a StringIO buffer to capture output
    renderer = TextualRenderer()
    output = StringIO()
    
    # WHEN rendering to the buffer (by redirecting stdout)
    with patch('sys.stdout', output):
        renderer.render(sample_view_state, Path("-")) # "-" signals stdout

    # THEN the output should match the expected tree structure
    expected_output = (
        "└── my_app\n"
        "    ├── Car\n"
        "    │   [C] -> my_app.Engine\n"
        "    └── Engine\n"
    )
    assert output.getvalue() == expected_output

def test_textual_renderer_to_file(sample_view_state: ViewState, tmp_path: Path):
    """Tests that the textual renderer can write to a specified file."""
    renderer = TextualRenderer()
    output_file = tmp_path / "output.txt"
    renderer.render(sample_view_state, output_file)

    content = output_file.read_text()
    assert "└── my_app" in content
    assert "[C] -> my_app.Engine" in content

def test_textual_renderer_empty_view_state():
    """Tests that the textual renderer produces no output for an empty view state."""
    renderer = TextualRenderer()
    output = StringIO()
    with patch('sys.stdout', output):
        renderer.render(ViewState(), Path("-"))
    
    assert output.getvalue() == ""