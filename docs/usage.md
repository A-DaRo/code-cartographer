# Code Cartographer - Usage Guide

Welcome to Code Cartographer, an interactive analysis tool designed to help you explore, understand, and document your Python codebases.

This guide provides practical examples and recipes for common use cases, from generating quick summaries in your terminal to launching a fully interactive exploration in your browser.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.8+**
2.  **The `code-cartographer` package**:
    ```sh
    pip install code-cartographer
    ```
3.  **Graphviz (System Package)**: For generating high-quality image diagrams (`.svg`, `.png`), you must have the Graphviz system package installed.
    *   **macOS (using Homebrew)**: `brew install graphviz`
    *   **Ubuntu/Debian**: `sudo apt-get install graphviz`
    *   **Windows (using Chocolatey)**: `choco install graphviz`

## 2. Core Concepts

Code Cartographer operates on a few key concepts. Understanding these will make using the tool intuitive.

*   **The `query` command**: This is the primary command for generating **static, non-interactive outputs** like images or text files.
*   **The `serve` command**: This command starts a **local web server** for the fully interactive browser-based experience.
*   **The Root (`--root`)**: This is the starting point for your exploration, specified as a Fully-Qualified Name (FQN), e.g., `my_project.services.PaymentService`.
*   **The Depth (`--depth`)**: This controls how many steps away from the root the analysis should traverse. A depth of `1` shows the root and its immediate neighbors.
*   **The Renderer (`--renderer`)**: This specifies the output format. The default is `graphviz`.

---

## 3. Recipes: Practical Examples

Here are several recipes to solve common software development and architecture tasks.

### Recipe 1: The Quick Terminal Overview

**Goal**: Quickly understand the immediate dependencies and inheritance of a single class directly from your terminal, with no external tools needed. This is perfect for a quick sanity check while coding.

**Command**:
We will use the `textual` renderer to get an ASCII-art style tree.

```sh
code-cartographer query . \
  --root my_project.services.PaymentService \
  --depth 1 \
  --renderer text
```

**How It Works**:
*   `query .`: We are asking for a static output, analyzing the project in the current directory.
*   `--root my_project.services.PaymentService`: We set our focus on the `PaymentService` class.
*   `--depth 1`: We only want to see classes that are directly connected to `PaymentService` (one step away).
*   `--renderer text`: We specify the output should be plain text. Since no `--output` is provided, it will be printed directly to your terminal.


**Expected Output**:
The output is a clean, hierarchical summary designed for easy reading in a terminal.

```
my_project.services.PaymentService
├── [I]nherits from: my_project.services.BaseService
├── [C]omposes: my_project.utils.StripeClient
├── [C]omposes: my_project.models.database.DatabaseConnection
└── [D]epends on: my_project.models.User
```
*The letters `[I]`, `[C]`, `[D]` are shorthand for Inheritance, Composition, and Dependency.*

### Recipe 2: Generating a High-Quality Diagram for Documentation

**Goal**: Create a clean, high-quality SVG diagram of a specific module to include in a README file, pull request description, or team wiki.

**Command**:
We will use the default `graphviz` renderer and specify an SVG output file.

```sh
code-cartographer query . \
  --root my_project.services \
  --depth 2 \
  --output services_architecture.svg
```

**How It Works**:
*   `query .`: We are asking for a static output, analyzing the project in the current directory.
*   `--root my_project.services`: We start our analysis at the package level. The tool will show all classes within this package and their connections.
*   `--depth 2`: We want to see the classes within the `services` package, their direct relationships, and the classes one step beyond that.
*   `--output services_architecture.svg`: The file extension `.svg` tells the `graphviz` renderer to produce a Scalable Vector Graphics file. If you used `.png`, it would produce a PNG image.


**Expected Output**:
A file named `services_architecture.svg` is created in your current directory. When opened, it will look like this (conceptually):


*(Conceptual image of a Graphviz diagram)*

The diagram will be cleanly laid out, with different shapes and colors for packages vs. classes, and different arrow styles for inheritance, composition, etc., making it immediately understandable.

### Recipe 3: The Deep Dive - Interactive Exploration

**Goal**: Freely explore the entire codebase, starting with a high-level view and interactively diving into specific areas of interest without regenerating a new file each time. This is the most powerful way to reverse-engineer and understand a complex system.

**Command**:
This uses the `serve` command to start the interactive session.

```sh
code-cartographer serve --project .
```

**How It Works**:
*   `serve`: This tells the tool to start its backend web server, not to generate a static file.
*   `--project .`: This tells the server to analyze the entire project in the current directory (`.`). The server will perform the full multi-pass analysis once at startup, building the complete Metamodel in memory.

**Expected Output**:
Your terminal will show that a server is running:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
🚀 Code Cartographer is ready for exploration. Open your browser to the URL above.
```

Now, open your web browser and navigate to `http://127.0.0.1:8000`. You will be greeted with the web-based Single Page Application (SPA).

**The Interactive Experience**:

> **Key Concept**: Unlike the `query` command, your actions in the browser do not re-parse the source code. They send lightweight queries to the Python backend, which queries its in-memory Metamodel and sends back only the data needed to render the new view. This makes the experience incredibly fast.

1.  **Initial View**: You'll see a high-level diagram of the root packages of your project.
2.  **Hovering**: Hover your mouse over a node (a package or class) to see a tooltip with its full FQN and other metadata.
3.  **Clicking (Focus)**: Click on the `my_project.services` package node. The diagram will smoothly animate and transition to a new view centered on that package, showing you the classes inside it. This action sent a new query to the backend: `{ "root_fqns": ["my_project.services"], "depth": 1 }`.
4.  **Using UI Controls**: Use the "Depth" slider in the UI to increase the visibility, revealing more distant relationships in real-time. Each change to a control sends a new query to the backend.
5.  **Filtering**: Use checkboxes in the UI to hide certain types of relationships (e.g., "Hide Dependencies") to declutter the view and focus on the structural backbone of your application.