import argparse
from pathlib import Path

from .construction.builders import AstModelBuilder
from .query_control.facade import AnalysisFacade
from .presentation.renderers import GraphvizRenderer, TextualRenderer
from .presentation.server import APIServer
from .query_control.query import Query

def main():
    """Main entry point for the Code Cartographer CLI."""
    parser = argparse.ArgumentParser(description="Code Cartographer: An advanced architectural analysis tool.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Render Command ---
    parser_render = subparsers.add_parser("render", help="Generate a static diagram file.")
    parser_render.add_argument("project_path", type=Path, help="Path to the root of the project to analyze.")
    parser_render.add_argument("--output", "-o", type=Path, required=True, help="Output file path (e.g., diagram.svg, tree.txt).")
    parser_render.add_argument("--format", "-f", choices=["graphviz", "text"], help="Output format. Inferred from output extension if not provided.")
    # Add more query-related args as needed...

    # --- Serve Command ---
    parser_serve = subparsers.add_parser("serve", help="Launch the interactive web server.")
    parser_serve.add_argument("project_path", type=Path, help="Path to the root of the project to analyze.")
    parser_serve.add_argument("--host", default="127.0.0.1", help="Host to bind the server to.")
    parser_serve.add_argument("--port", type=int, default=8000, help="Port to run the server on.")

    args = parser.parse_args()

    # --- Command Execution ---
    builder = AstModelBuilder()
    facade = AnalysisFacade(builder)
    
    project_name = args.project_path.name
    print(f"🏗️ Loading project '{project_name}' from: {args.project_path}")
    facade.load_project(args.project_path, project_name)
    print("✅ Project loaded successfully.")

    if args.command == "render":
        # Create a default query that shows the whole project structure
        initial_query = Query(root_fqns=[project_name], depth=100)
        view_state = facade.execute_query(initial_query)

        output_format = args.format
        if not output_format:
            if args.output.suffix in ['.svg', '.png', '.pdf', '.dot']:
                output_format = 'graphviz'
            else:
                output_format = 'text'
        
        renderer = GraphvizRenderer() if output_format == 'graphviz' else TextualRenderer()
        
        print(f"🎨 Rendering to {args.output} using {output_format} renderer...")
        renderer.render(view_state, args.output)
        print("✨ Done.")

    elif args.command == "serve":
        server = APIServer(facade)
        server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()