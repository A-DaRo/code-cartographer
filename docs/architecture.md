# Code Cartographer Architecture

This document outlines the high-level architecture of the Code Cartographer
system. The design is based on a layered approach, ensuring a strong
separation of concerns between data representation, data collection, and
data presentation.

## Core Philosophy: The Codebase as a Queryable Database

We treat the target codebase not as a source for a single, static diagram, but
as a database. The tool's primary function is to build a rich, in-memory
representation of this database (the Metamodel) and provide the means to
interactively query and visualize it.

---

### Layer 1: The Metamodel

The logical core of the system is the Metamodel, a pure data representation of
the target codebase. It has zero dependencies on other layers.

**Key Design Patterns:**
*   **Composite Pattern**: The entire codebase is modeled as a hierarchical tree of `CodeUnit` objects (`PackageUnit`, `ModuleUnit`, `ClassifierUnit`). This allows clients to treat individual objects and compositions of objects uniformly and enables powerful, structure-aware queries.
*   **First-Class Objects**: Relationships are not mere pointers between nodes but are treated as first-class `Relationship` objects. This allows them to hold rich metadata and makes them independently queryable.

**Components:**
*   **`metamodel.elements`**: Defines the `CodeUnit` abstract base class and its concrete implementations, which form the nodes of the project hierarchy.
*   **`metamodel.relationship`**: Defines the `Relationship` data class and `RelationshipType` enum. These objects represent the edges in the project graph.
*   **`metamodel.model`**: Defines the `Metamodel` class, a root container that holds the entire hierarchy and provides indexed registries for fast O(1) lookup of any `CodeUnit` by its fully-qualified name (FQN).

### Layer 2: The Construction Layer

The Construction Layer is the engine that populates the Metamodel. It bridges the gap between raw source code and the clean, abstract representation defined by the Metamodel.

**Key Design Patterns:**
*   **Builder Pattern**: The `AstModelBuilder` acts as the director for the construction process. It provides a simple, clean interface (`build(path)`) that hides the complex, multi-pass logic required to build the model. This decouples the application's main logic from the details of parsing.
*   **Visitor Pattern**: The actual AST traversal is delegated to specialized `ast.NodeVisitor` classes (`HierarchicalVisitor`, `RelationshipVisitor`). Each visitor is responsible for a single concern, making the parsing logic modular and easier to maintain.
*   **Multi-Pass Strategy**: The builder uses a two-pass approach to solve the problem of forward references in code.
    1.  **Hierarchy Pass**: The `HierarchicalVisitor` scans all files to identify every package, module, and class, populating the Metamodel's FQN registry. At this stage, it only notes *what* exists, not how things are connected.
    2.  **Relationship Pass**: With a complete FQN registry, the `RelationshipVisitor` re-scans the files. It can now reliably resolve any type name it encounters (e.g., a base class, a type hint) to its FQN and create the appropriate `Relationship` object.

**Components:**
*   **`construction.builders`**: Defines the public `IModelBuilder` interface and its concrete `AstModelBuilder` implementation. This is the primary entry point to this layer.
*   **`construction.visitors`**: Contains the internal visitor classes that handle the low-level details of traversing the source code's Abstract Syntax Tree.

### Layer 3: The Query & Control Layer

This layer serves as the primary Application Programming Interface (API) for the entire system. It decouples clients (like a UI) from the internal complexity of the `Metamodel` and its construction. It is designed to be the single point of entry for all analytical and interactive operations.

**Key Design Patterns:**
*   **Facade Pattern**: The `AnalysisFacade` class is the cornerstone of this layer. It provides a simple, clean, and stable interface (`load_project()`, `execute_query()`) that hides the underlying complexity of builders, visitors, and graph traversal. All client interactions flow through this facade.
*   **Data Transfer Object (DTO)**: The `Query` and `ViewState` classes are immutable and serializable DTOs.
    *   `Query`: Encapsulates a client's *request* for a specific view of the code.
    *   `ViewState`: Encapsulates the *result* of that request in a simple, flat format, ready for any presentation layer. This ensures the presentation layer is completely decoupled from the `Metamodel`.
*   **Command Pattern**: The `ICommand` interface and its concrete implementations (`FocusOnNodeCommand`, etc.) encapsulate user actions as objects. This allows for a clean separation between the UI and the application logic, enabling features like history, undo/redo, and easy testing of user interactions.

**Control Flow:**
1.  A client (e.g., a CLI or GUI controller) instantiates an `AnalysisFacade`.
2.  The client calls `facade.load_project()` to build the `Metamodel`.
3.  The client creates an initial `Query` object.
4.  To display or update the view, the client calls `facade.execute_query(query)`, which returns a `ViewState` DTO.
5.  The `ViewState` is passed to the Presentation Layer for rendering.
6.  When the user interacts with the UI (e.g., clicks a button), the UI controller creates a `Command` object and uses it to update the current `Query` state, then repeats step 4.

**Components:**
*   **`query_control.facade`**: Defines the `AnalysisFacade`, the main entry point to the system.
*   **`query_control.query`**: Defines the `Query` object for specifying requests.
*   **`query_control.view_state`**: Defines the `ViewState` object for returning results.
*   **`query_control.commands`**: Defines the command objects for managing interactive state changes.

### Layer 4: The Presentation Layer

The final layer is responsible for rendering the results of a query into a human-readable format. It is completely decoupled from the `Metamodel` and interacts only with the `ViewState` DTO provided by the Query & Control Layer.

**Key Design Patterns:**
*   **Strategy Pattern**: The core of this layer is the `IRenderer` interface. Different concrete classes (`GraphvizRenderer`, `TextualRenderer`) implement this interface, providing interchangeable "strategies" for visualization. This makes the system highly extensible—a new output format (e.g., JSON, Mermaid.js) can be added simply by creating a new class that implements the `IRenderer` interface, with no changes needed to the core application logic.

**Control Flow:**
1.  After the client receives a `ViewState` object from the `AnalysisFacade`, it decides which rendering strategy to use.
2.  It instantiates the chosen renderer class (e.g., `renderer = GraphvizRenderer()`).
3.  It calls `renderer.render(view_state, output_path)` to generate the final output.

**Available Strategies:**
*   **`GraphvizRenderer`**: Generates high-quality, graphical diagrams in formats like SVG, PNG, and PDF. It produces a professional and easy-to-understand visualization of the codebase structure. It requires the `graphviz` Python library and the Graphviz system package to be installed.
    *   **Use Case**: Ideal for generating documentation, presentations, or for detailed visual analysis.
*   **`TextualRenderer`**: Generates a lightweight, hierarchical tree view of the codebase directly in the console or a text file. It has no external dependencies.
    *   **Use Case**: Perfect for quick, command-line based analysis and for environments where graphical tools are unavailable.

### Layer 5: The API & Server Layer

To enable a rich, interactive frontend experience, the backend is exposed via a client-server model. The Presentation Layer is extended with a web server that serves structured data (JSON) over a web API, replacing the direct generation of static files.

**Key Technologies:**
*   **FastAPI**: A modern, high-performance Python web framework used to build the API. It provides automatic data validation (using Pydantic), serialization, and API documentation (via OpenAPI/Swagger).
*   **Uvicorn**: An ASGI server that runs the FastAPI application.

**Architecture:**
1.  **Client-Server Model**: The application is split into a Python backend (the server) and a JavaScript frontend (the client). The frontend is now responsible for all rendering and user interaction.
2.  **JSON API**: The server exposes a `/api/v1/query` endpoint. The frontend sends a `Query` object as a JSON payload in a `POST` request.
3.  **Backend Processing**: The `APIServer` receives the request, validates the payload, passes the `Query` to the `AnalysisFacade`, and gets a `ViewState` in return.
4.  **Serialization**: A new `JsonSerializer` transforms the `ViewState` DTO into a clean, JSON-serializable dictionary, ensuring enums and other Python-specific types are converted to simple strings.
5.  **Response**: The server sends the JSON payload back to the frontend, which then uses a graph rendering library (like Cytoscape.js or React Flow) to visualize the data.

**The Interactive Loop:**
The core of the user experience is a loop:
1.  User interacts with the frontend UI (e.g., clicks a node).
2.  The frontend updates its internal `queryState`.
3.  This state change triggers an API call to the backend with the new query.
4.  The backend processes the query and returns a new `ViewState`.
5.  The frontend receives the new data and re-renders the visualization.