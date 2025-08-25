# Code Cartographer 🗺️

**Reverse-engineer and explore your Python codebases with interactive, on-demand diagrams.**

Code Cartographer is an architectural analysis tool that goes beyond static diagram generation. It parses your Python project and launches an interactive web-based interface, allowing you to explore your system's structure, relationships, and complexity in real time.


*(Conceptual GIF showing a user clicking on packages to expand and explore a codebase)*

## Core Features

*   **🔎 Static & Dynamic Analysis**: Builds a complete model of your codebase by analyzing source files.
*   **🌐 Interactive Web UI**: Launches a local web server to provide a fast, interactive graph for exploration. No need to regenerate diagrams for every change in perspective.
*   **📸 Static Diagram Generation**: Exports high-quality SVG/PNG diagrams for documentation, code reviews, and presentations.
*   **💻 Terminal-Friendly Output**: Provides a quick, text-based summary of a class or module's relationships directly in your terminal.
*   **🔌 Extensible Exporters**: Can export the project's structure to standard formats like GraphML for use in advanced analysis tools like Gephi or Neo4j.

## Installation

To get started, you'll need Python 3.8+ and the Graphviz system package.

1.  **Install Graphviz**:
    *   **macOS**: `brew install graphviz`
    *   **Ubuntu/Debian**: `sudo apt-get install graphviz`
    *   **Windows**: `choco install graphviz`

2.  **Install Code Cartographer**:
    ```sh
    pip install code-cartographer
    ```

## Quick Start: Interactive Exploration

The best way to experience Code Cartographer is through its interactive `serve` command.

1.  Navigate to the root directory of a Python project you want to analyze.
2.  Run the `serve` command:
    ```sh
    code-cartographer serve --project .
    ```
3.  The tool will analyze your project and start a local web server. Open your browser to the URL provided (usually `http://127.0.0.1:8000`).

You can now explore your entire codebase by hovering, clicking, and expanding nodes in the diagram.

## Basic Usage: Static Diagrams

Need a diagram for your documentation? Use the `query` command.

**Generate an SVG diagram of a specific service:**
```sh
code-cartographer query \
  --root my_project.services.PaymentService \
  --depth 2 \
  --output payment_service.svg
```

**Get a quick summary in your terminal:**
```sh
code-cartographer query \
  --root my_project.services.PaymentService \
  --renderer text
```

## Full Documentation

For a complete guide to all commands, renderers, and advanced use cases, please see our detailed **[Usage Guide](./docs/usage.md)**.

## Contributing

Contributions are welcome! Please read our contributing guide to get started.

## License

This project is licensed under the MIT License.