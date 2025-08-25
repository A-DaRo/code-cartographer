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

    # --- Query Command ---
    parser_query = subparsers.add_parser("query", help="Generate a static diagram or textual output based on a query.")
    parser_query.add_argument("project_path", type=Path, help="Path to the root of the project to analyze.")
    parser_query.add_argument("--root", "-r", type=str, required=True, help="Root FQN (e.g., 'my_project.main') to start the analysis from.")
    parser_query.add_argument("--depth", "-d", type=int, default=2, help="Analysis depth from the root.")
    parser_query.add_argument("--output", "-o", type=Path, default=None, help="Output file path. If not provided for text renderer, prints to console.")
    parser_query.add_argument("--renderer", choices=["graphviz", "text"], help="Output format. Inferred from output extension if not provided.")

    # --- Serve Command ---
    parser_serve = subparsers.add_parser("serve", help="Launch the interactive web server.")
    parser_serve.add_argument("--project", type=Path, default=".", help="Path to the root of the project to analyze.")
    parser_serve.add_argument("--host", default="127.0.0.1", help="Host to bind the server to.")
    parser_serve.add_argument("--port", type=int, default=8000, help="Port to run the server on.")

    args = parser.parse_args()

    # --- Command Execution ---
    builder = AstModelBuilder()
    facade = AnalysisFacade(builder)
    
    project_path_arg = args.project_path if hasattr(args, 'project_path') else args.project
    # Resolve the path to get a more reliable name and absolute path
    project_path = project_path_arg.resolve()
    project_name = project_path.name
    if not project_name:
        raise ValueError(f"Could not determine a project name from path '{project_path_arg}'. Please provide a valid project path.")
    
    print(f"🏗️ Loading project '{project_name}' from: {project_path}")
    facade.load_project(project_path, project_name)
    print("✅ Project loaded successfully.")

    if args.command == "query":
        # Normalize the root FQN provided by the user.
        user_root_fqn = args.root
        
        # Handle special case for querying the project root.
        if user_root_fqn == '.':
            corrected_root_fqn = project_name
        # If the user-provided FQN already starts with the project name, use it as is.
        # Otherwise, prepend the project name to create the full internal FQN.
        elif user_root_fqn.startswith(f"{project_name}."):
            corrected_root_fqn = user_root_fqn
        else:
            corrected_root_fqn = f"{project_name}.{user_root_fqn}"
        
        # Use the corrected FQN to create the query
        query = Query(root_fqns=[corrected_root_fqn], depth=args.depth)
        
        
        view_state = facade.execute_query(query)

        # Determine renderer from argument or file extension
        renderer_choice = args.renderer
        if not renderer_choice:
            if args.output and args.output.suffix in ['.svg', '.png', '.pdf', '.dot']:
                renderer_choice = 'graphviz'
            else:
                renderer_choice = 'text'
        
        # Validate arguments for the chosen renderer
        if renderer_choice == 'graphviz' and not args.output:
            parser.error("The --output flag is required for the 'graphviz' renderer.")

        renderer = GraphvizRenderer() if renderer_choice == 'graphviz' else TextualRenderer()
        
        output_destination = args.output
        if not output_destination and renderer_choice == 'text':
            output_destination = Path("-") # Special path for stdout

        if str(output_destination) == "-":
            print(f"🎨 Rendering output to console using {renderer_choice} renderer...")
        else:
            print(f"🎨 Rendering to {output_destination} using {renderer_choice} renderer...")
        
        renderer.render(view_state, output_destination)
        
        if str(output_destination) != "-":
            print("✨ Done.")

    elif args.command == "serve":
        server = APIServer(facade)
        server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main()