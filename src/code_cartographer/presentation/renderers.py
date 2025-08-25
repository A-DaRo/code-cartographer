from __future__ import annotations
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from collections import defaultdict
from typing import TYPE_CHECKING, List, Dict, Any

from ..exceptions import RenderingError

if TYPE_CHECKING:
    import graphviz
    from ..query_control.view_state import ViewState

class IRenderer(ABC):
    """
    Abstract Base Class defining the interface for a rendering strategy.

    A renderer is responsible for consuming a ViewState Data Transfer Object (DTO)
    and producing a specific output, such as an image file or console text.
    This interface ensures that the application can use any rendering strategy
    interchangeably.
    The public `render` method defines the skeleton of the rendering algorithm,
    delegating the format-specific implementation details to subclasses.
    """
    def render(self, view_state: ViewState, output_path: Path) -> None:
        """
        The template method. It orchestrates the rendering process.
        It should not be overridden by subclasses.

        Args:
            view_state: The ViewState DTO returned from the AnalysisFacade.
            output_path: A pathlib.Path object indicating where to save the
                         output. A path of "-" signals writing to stdout.

        Raises:
            RenderingError: If the rendering process fails.
        """
        if not view_state.nodes:
            self._handle_empty_view(output_path)
            return

        # 1. Prepare common data structures
        self._prepare_data(view_state, output_path)

        # 2. Let the subclass render the actual output
        canvas_content = self._render_canvas()

        # 3. Finalize and write the output
        self._write_output(canvas_content)

    def _prepare_data(self, view_state: ViewState, output_path: Path):
        """
        A concrete helper method to set up common data structures that all
        renderers might need.
        """
        self._view_state = view_state
        self._output_path = output_path
        self.nodes_by_fqn = {n['fqn']: n for n in self._view_state.nodes}
        self.edges_by_source = defaultdict(list)
        self.edges_by_target = defaultdict(list)
        for edge in self._view_state.edges:
            self.edges_by_source[edge['source_fqn']].append(edge)
            self.edges_by_target[edge['target_fqn']].append(edge)
        
        # The original logic was too strict, preventing children from appearing if their
        # parent wasn't also explicitly in the view_state's node list.
        self.children_by_parent = defaultdict(list)
        for node in self._view_state.nodes:
            parent_fqn = node.get('parent_fqn')
            if parent_fqn: # A node can only be a child if it has a parent_fqn.
                 self.children_by_parent[parent_fqn].append(node)
        
        # Identify the explicit root nodes for the diagram
        self.explicit_root_nodes = [
            n for n in self._view_state.nodes if n['fqn'] in self._view_state.root_fqns
        ]
        
        # Pre-sort for consistent output
        self.explicit_root_nodes.sort(key=lambda n: n['name'])
        for children in self.children_by_parent.values():
            children.sort(key=lambda n: n['name'])
    
    def _handle_empty_view(self, output_path: Path):
        """Handles the case where there is nothing to render."""
        if str(output_path) == "-":
            sys.stdout.write("No elements found for the given query.\n")

    def _write_output(self, content: str | None):
        """
        Writes the finalized content to the specified output path.
        This method is safe to call with `None` content.
        """
        if str(self._output_path) == "-":
            # Only write to stdout if there is actual content.
            if content is not None:
                sys.stdout.write(content)
        else:
            # For file output, we only write if content is provided.
            # This correctly handles Graphviz which writes its own file and returns None.
            if content:
                try:
                    self._output_path.write_text(content, encoding="utf-8")
                except IOError as e:
                    raise RenderingError(f"Failed to write to file {self._output_path}: {e}") from e

    @abstractmethod
    def _render_canvas(self) -> str | None:
        """
        The primary abstract method for subclasses to implement.

        This method is responsible for generating the final output content
        as a string (for text-based formats) or writing a file directly and
        returning None (for binary/complex formats like Graphviz).
        """
        raise NotImplementedError

class GraphvizRenderer(IRenderer):
    """
    A concrete rendering strategy that generates a diagram image file (e.g., SVG, PNG)
    from a ViewState using the Graphviz library.

    This renderer translates the abstract nodes and edges from the ViewState into
    the DOT graph description language, applying semantic styling based on the
    metadata of the elements. It requires the Graphviz system package to be
    installed on the host machine.
    """
    def __init__(self):
        try:
            import graphviz
            self._graphviz = graphviz
        except ImportError:
            raise ImportError("The 'graphviz' library is required for GraphvizRenderer. Please run 'pip install graphviz'.")

    def _render_canvas(self) -> None:
        """Generates the Graphviz diagram and writes it directly to a file."""
        dot = self._graphviz.Digraph()
        dot.attr('graph', rankdir='TB', splines='ortho')

        self._add_nodes(dot, self._view_state.nodes)
        self._add_edges(dot, self._view_state.edges)
        
        output_base = str(self._output_path.with_suffix(''))
        output_format = self._output_path.suffix.lstrip('.')

        if not output_format:
            raise RenderingError("Output file for GraphvizRenderer must have an extension (e.g., .png, .svg).")

        try:
            dot.render(output_base, format=output_format, view=False, cleanup=True)
        except Exception as e:
            msg = (
                "Failed to execute Graphviz. Is it installed and in your system's PATH?\n"
                f"Original error: {e}"
            )
            raise RenderingError(msg) from e
        
        # Since graphviz writes the file itself, we return None.
        return None

    def _add_nodes(self, dot: "graphviz.Digraph", nodes: List[Dict]) -> None:
        for node_data in nodes:
            style_attrs = self._get_node_style(node_data)
            dot.node(name=node_data['fqn'], **style_attrs)

    def _get_node_style(self, node_data: Dict) -> Dict:
        style = {'shape': 'plain'}
        bg_color = {
            'package': '#E6F2FA', # Light Blue
            'class': '#FFFFFF',   # White
            'module': '#F5F5F5',  # Light Grey
        }.get(node_data['element_type'], '#CCCCCC') # Default Grey
        
        # Use a single, multi-line f-string for robustness with the dot parser.
        # This ensures a clean string is passed to the graphviz library.
        label_str = f'''<
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
        <TR><TD BGCOLOR="{bg_color}"><B>{node_data["name"]}</B></TD></TR>
        </TABLE>
        >'''

        style['label'] = label_str
        return style

    def _add_edges(self, dot: "graphviz.Digraph", edges: List[Dict]) -> None:
        for edge_data in edges:
            style_attrs = self._get_edge_style(edge_data)
            dot.edge(
                edge_data['source_fqn'],
                edge_data['target_fqn'],
                **style_attrs
            )

    def _get_edge_style(self, edge_data: Dict) -> Dict:
        rel_type = edge_data['relationship_type']
        styles = {
            'INHERITANCE': {'arrowhead': 'empty', 'dir': 'back'},
            'COMPOSITION': {'arrowhead': 'diamond', 'style': 'dashed'},
            'AGGREGATION': {'arrowhead': 'odiamond', 'style': 'dashed'},
            'ASSOCIATION': {'arrowhead': 'vee', 'style': 'dotted'},
            'DEPENDENCY': {'arrowhead': 'normal', 'style': 'dashed'},
        }
        return styles.get(rel_type, {'arrowhead': 'normal'})

class TextualRenderer(IRenderer):
    """
    A concrete rendering strategy that generates a hierarchical, tree-like
    textual representation of a ViewState, printed to a file or standard output.
    """
    def _render_canvas(self) -> str:
        """Generates the textual representation as a single string."""
        # The root nodes for rendering MUST be the ones specified in the query.
        # The query facade ensures these nodes are included in the view_state.
        valid_root_nodes = [
            self.nodes_by_fqn[root_fqn]
            for root_fqn in self._view_state.root_fqns
            if root_fqn in self.nodes_by_fqn
        ]

        # If for some reason the query root isn't in the node list, that's an
        # error state from the query phase. We should not fall back to guessing.
        if not valid_root_nodes:
            # The _handle_empty_view method handles the case where the initial
            # query returned no nodes at all. This message is for when the query
            # returned nodes, but not the specific root we asked to render from.
            return "Query Error: The specified root was not found in the analysis results.\n"

        valid_root_nodes.sort(key=lambda n: n['name'])
        
        output_lines = []
        for i, root in enumerate(valid_root_nodes):
            self._render_node_recursive(
                root, "", i == len(valid_root_nodes) - 1, output_lines,
                self.children_by_parent
            )
        
        return "\n".join(output_lines) + "\n"

    def _render_node_recursive(
        self,
        node: Dict,
        prefix: str,
        is_last_sibling: bool,
        output_lines: List[str],
        children_map: Dict[str, List[Dict]],
    ):
        connector = "└── " if is_last_sibling else "├── "
        output_lines.append(f"{prefix}{connector}{node['name']}")
        
        new_prefix = prefix + ("    " if is_last_sibling else "│   ")
        
        outgoing = sorted(self.edges_by_source.get(node['fqn'], []), key=lambda e: e['target_fqn'])
        incoming = sorted(self.edges_by_target.get(node['fqn'], []), key=lambda e: e['source_fqn'])
        children = children_map.get(node['fqn'], [])
        
        total_items = len(outgoing) + len(incoming) + len(children)
        items_rendered = 0

        for edge in outgoing:
            items_rendered += 1
            rel_prefix = new_prefix + ("└── " if items_rendered == total_items else "├── ")
            rel_char = self._get_rel_char(edge['relationship_type'])
            output_lines.append(f"{rel_prefix}[{rel_char}] -> {edge['target_fqn']}")

        for edge in incoming:
            items_rendered += 1
            if edge['source_fqn'] == node['fqn']: continue
            rel_prefix = new_prefix + ("└── " if items_rendered == total_items else "├── ")
            rel_char = self._get_rel_char(edge['relationship_type'])
            output_lines.append(f"{rel_prefix}[{rel_char}] <- Used by {edge['source_fqn']}")
        
        for child in children:
            items_rendered += 1
            self._render_node_recursive(
                child, new_prefix, items_rendered == total_items, output_lines,
                children_map
            )

    def _get_rel_char(self, rel_type: str) -> str:
        return {
            'INHERITANCE': 'I',
            'COMPOSITION': 'C',
            'AGGREGATION': 'A',
            'ASSOCIATION': 'S',
            'DEPENDENCY': 'D',
        }.get(rel_type, '?')