/** Represents the query sent to the backend. */
export interface Query {
  root_fqns: string[];
  depth: number;
  filter_rules: Record<string, any>[];
}

/** Represents a single node in the view. */
export interface ViewNode {
  fqn: string;
  name: string;
  element_type: 'package' | 'class' | 'module';
  parent_fqn: string | null;
}

/** Represents a single edge in the view. */
export interface ViewEdge {
  source_fqn: string;
  target_fqn: string;
  relationship_type: 'INHERITANCE' | 'COMPOSITION' | 'ASSOCIATION' | 'DEPENDENCY' | 'AGGREGATION';
}

/** The complete data structure returned by the backend for a query. */
export interface ViewState {
  nodes: ViewNode[];
  edges: ViewEdge[];
}

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

/**
 * Sends a query to the backend API and retrieves the corresponding ViewState.
 * @param query - The Query object specifying the desired view.
 * @param signal - An AbortSignal to allow for cancellation of the request.
 * @returns A Promise that resolves with the ViewState.
 * @throws Will throw an error if the network request fails or the API returns an error.
 */
export async function executeQuery(query: Query, signal: AbortSignal): Promise<ViewState> {
  const endpoint = `${API_URL}/api/v1/query`;
  
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(query),
    signal,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorBody}`);
  }

  return (await response.json()) as ViewState;
}