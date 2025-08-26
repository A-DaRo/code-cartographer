// ====================================================================================
// TYPE DEFINITIONS - Describes the contract between the frontend and backend.
// ====================================================================================

/**
 * Enum-like object for the different types of code elements.
 * Using this prevents magic strings in the code.
 */
export const ElementType = {
  PACKAGE: 'package',
  MODULE: 'module',
  CLASS: 'class',
} as const;

/**
 * Enum-like object for the different types of relationships.
 */
export const RelationshipType = {
  INHERITANCE: 'INHERITANCE',
  COMPOSITION: 'COMPOSITION',
  ASSOCIATION: 'ASSOCIATION',
  DEPENDENCY: 'DEPENDENCY',
  AGGREGATION: 'AGGREGATION',
} as const;

// Utility types to extract the string literal types from the const objects above.
type ValueOf<T> = T[keyof T];
type ElementTypeValue = ValueOf<typeof ElementType>;
type RelationshipTypeValue = ValueOf<typeof RelationshipType>;

/** Represents a single node in the view graph. */
export interface ViewNode {
  fqn: string;
  name: string;
  element_type: ElementTypeValue;
  parent_fqn: string | null;
}

/** Represents a single edge connecting two nodes in the view graph. */
export interface ViewEdge {
  source_fqn: string;
  target_fqn: string;
  relationship_type: RelationshipTypeValue;
}

/** The complete data structure for a single view, returned by the backend. */
export interface ViewState {
  nodes: ViewNode[];
  edges: ViewEdge[];
}

/** The query payload sent to the backend to request a specific view. */
export interface Query {
  root_fqns: string[];
  depth: number;
  filter_rules: Record<string, any>[];
}

/** The initial project metadata fetched on application load. */
export interface ProjectInfo {
  project_name: string;
  root_fqns: string[];
}

// ====================================================================================
// API CLIENT IMPLEMENTATION
// ====================================================================================

const API_BASE_URL = '/api/v1';
const PROJECT_INFO_ENDPOINT = `${API_BASE_URL}/project-info`;
const QUERY_ENDPOINT = `${API_BASE_URL}/query`;

/**
 * Custom error class for API-related failures.
 * Contains the HTTP status for more specific error handling.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly statusText: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * A generic, reusable fetch helper for the Code Cartographer API.
 * @param endpoint - The API endpoint to request.
 * @param options - Standard fetch RequestInit options.
 * @throws {ApiError} - If the network response is not OK.
 */
async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(endpoint, options);

  if (!response.ok) {
    const errorBody = await response.text();
    const errorMessage = `API Error: ${errorBody || response.statusText}`;
    throw new ApiError(errorMessage, response.status, response.statusText);
  }

  return (await response.json()) as T;
}

/**
 * A namespaced object containing all methods for interacting with the backend API.
 */
export const ApiClient = {
  /**
   * Fetches initial project information from the backend.
   * @param signal - An AbortSignal to allow for cancellation.
   * @returns A Promise that resolves with the ProjectInfo.
   */
  getProjectInfo(signal?: AbortSignal): Promise<ProjectInfo> {
    return apiFetch<ProjectInfo>(PROJECT_INFO_ENDPOINT, { signal });
  },

  /**
   * Sends a query to the backend and retrieves the corresponding ViewState.
   * @param query - The Query object specifying the desired view.
   * @param signal - An AbortSignal to allow for cancellation.
   * @returns A Promise that resolves with the ViewState.
   */
  executeQuery(query: Query, signal: AbortSignal): Promise<ViewState> {
    return apiFetch<ViewState>(QUERY_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
      signal,
    });
  },
};