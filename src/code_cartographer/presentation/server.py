from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .serializers import JsonSerializer
from ..query_control.query import Query as InternalQuery # Keep internal logic separate
from ..metamodel.relationship import RelationshipType

if TYPE_CHECKING:
    from ..query_control.facade import AnalysisFacade

# Pydantic models for API request validation
class APIQuery(BaseModel):
    """Pydantic model for validating incoming query requests."""
    root_fqns: List[str] = Field(default_factory=list)
    depth: int = 1
    filter_rules: List[Dict[str, Any]] = Field(default_factory=list)

    def to_internal(self) -> InternalQuery:
        """Converts the API model to the internal Query dataclass."""
        return InternalQuery(
            root_fqns=self.root_fqns,
            depth=self.depth,
            filter_rules=self.filter_rules,
        )

class APIServer:
    """
    Provides the web server and API endpoints for interactive analysis.

    This server uses FastAPI to expose the functionality of the AnalysisFacade
    over HTTP. It handles incoming query requests from the frontend, passes
    them to the facade, and returns the resulting ViewState as a JSON response.
    """
    def __init__(self, facade: AnalysisFacade):
        """
        Initializes the server and injects the AnalysisFacade. It sets up the
        API routes (endpoints).
        """
        self._facade = facade
        self._app = FastAPI(title="Code Cartographer API")
        self._setup_middleware()
        self._setup_routes()

    @property
    def app(self) -> FastAPI:
        """Exposes the FastAPI app instance, primarily for testing."""
        return self._app

    def _setup_middleware(self):
        # Allow CORS for frontend development
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"], # In production, restrict to the frontend's domain
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        self._app.add_api_route("/api/v1/project-info", self.get_project_info, methods=["GET"], tags=["Project"])
        self._app.add_api_route("/api/v1/status", self.get_status, methods=["GET"], tags=["Status"])
        self._app.add_api_route("/api/v1/query", self.handle_query, methods=["POST"], tags=["Query"])

    async def get_project_info(self) -> Dict[str, Any]:
        """Returns the project's name and top-level FQNs."""
        project_info = self._facade.get_project_info()
        return project_info

    async def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the server."""
        return {
            "status": "ok",
            "project_loaded": self._facade._model is not None,
        }

    async def handle_query(self, query: APIQuery) -> Dict[str, Any]:
        """
        The main API endpoint. It accepts a query, executes it via the
        facade, and returns a serialized ViewState.
        """
        project_name = self._facade.get_project_info()["project_name"]
        
        normalized_fqns = []
        for fqn in query.root_fqns:
            # This logic is identical to the one in __main__.py
            if fqn == '.' or fqn == project_name:
                normalized_fqns.append(project_name)
            elif fqn.startswith(f"{project_name}."):
                normalized_fqns.append(fqn)
            else:
                normalized_fqns.append(f"{project_name}.{fqn}")
        
        # Create a new query object with the corrected FQNs
        internal_query = InternalQuery(
            root_fqns=normalized_fqns,
            depth=query.depth,
            filter_rules=query.filter_rules,
        )
        
        view_state = self._facade.execute_query(internal_query)
        
        serializer = JsonSerializer()
        response_data = serializer.serialize(view_state)
        return response_data

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Starts the Uvicorn web server."""
        print(f"🚀 Starting Code Cartographer server at http://{host}:{port}")
        print(f"📝 API documentation available at http://{host}:{port}/docs")
        uvicorn.run(self._app, host=host, port=port)