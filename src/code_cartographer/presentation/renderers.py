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
    """
    @abstractmethod
    def render(self, view_state: ViewState, output_path: Path) -> None:
        """
        The primary method of any renderer. It takes the complete ViewState
        and a target path and generates the corresponding output.

        Args:
            view_state: The ViewState DTO returned from the AnalysisFacade.
            output_path: A pathlib.Path object indicating where to save the
                         output. A path of "-" signals writing to stdout.

        Raises:
            RenderingError: If the rendering process fails.
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

    def render(self, view_state: ViewState, output_path: Path) -> None:
        dot = self._graphviz.Digraph()
        dot.attr('graph', rankdir='TB', splines='ortho')

        self._add_nodes(dot, view_state.nodes)
        self._add_edges(dot, view_state.edges)
        
        output_base = str(output_path.with_suffix(''))
        output_format = output_path.suffix.lstrip('.')

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
        
        # Using HTML-like labels for custom styling
        label_str = (
            f'<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
            f'<TR><TD BGCOLOR="{bg_color}"><B>{node_data["name"]}</B></TD></TR>'
            f'</TABLE>'
        )
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

    This renderer is lightweight, has no external dependencies, and is ideal for
    quick command-line analysis. It primarily uses the parent-child relationships
    of the nodes to build the tree.
    """
    def render(self, view_state: ViewState, output_path: Path) -> None:
        if not view_state.nodes:
            return

        nodes_by_fqn = {n['fqn']: n for n in view_state.nodes}
        children_by_parent_fqn = defaultdict(list)
        for node in view_state.nodes:
            parent_fqn = node.get('parent_fqn')
            if parent_fqn:
                children_by_parent_fqn[parent_fqn].append(node)
        
        edges_by_source_fqn = defaultdict(list)
        for edge in view_state.edges:
            edges_by_source_fqn[edge['source_fqn']].append(edge)

        # Find the roots of the tree (nodes whose parent is not in the view)
        root_nodes = [
            n for n in view_state.nodes 
            if n.get('parent_fqn') is None or n.get('parent_fqn') not in nodes_by_fqn
        ]
        # Sort roots and children for consistent output
        root_nodes.sort(key=lambda n: n['name'])
        for children in children_by_parent_fqn.values():
            children.sort(key=lambda n: n['name'])

        output_lines = []
        for i, root in enumerate(root_nodes):
            self._render_node_recursive(
                root, "", i == len(root_nodes) - 1, output_lines,
                children_by_parent_fqn, edges_by_source_fqn
            )
        
        output_str = "\n".join(output_lines) + "\n"

        if str(output_path) == "-":
            sys.stdout.write(output_str)
        else:
            try:
                output_path.write_text(output_str, encoding="utf-8")
            except IOError as e:
                raise RenderingError(f"Failed to write to file {output_path}: {e}") from e

    def _render_node_recursive(
        self,
        node: Dict,
        prefix: str,
        is_last: bool,
        output_lines: List[str],
        children_map: Dict[str, List[Dict]],
        edges_map: Dict[str, List[Dict]],
    ):
        connector = "└── " if is_last else "├── "
        output_lines.append(f"{prefix}{connector}{node['name']}")
        
        new_prefix = prefix + ("    " if is_last else "│   ")

        # Render relationships for this node
        if node['fqn'] in edges_map:
            for edge in sorted(edges_map[node['fqn']], key=lambda e: e['target_fqn']):
                rel_char = self._get_rel_char(edge['relationship_type'])
                output_lines.append(f"{new_prefix}[{rel_char}] -> {edge['target_fqn']}")

        # Recurse for children
        children = children_map.get(node['fqn'], [])
        for i, child in enumerate(children):
            self._render_node_recursive(
                child, new_prefix, i == len(children) - 1, output_lines,
                children_map, edges_map
            )

    def _get_rel_char(self, rel_type: str) -> str:
        return {
            'INHERITANCE': 'I',
            'COMPOSITION': 'C',
            'AGGREGATION': 'A',
            'ASSOCIATION': 'S',
            'DEPENDENCY': 'D',
        }.get(rel_type, '?')