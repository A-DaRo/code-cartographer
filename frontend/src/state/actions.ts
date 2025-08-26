import type { ViewState } from '../api/client';

/** The discriminated union of all possible state management actions. */
export type Action =
  | { type: 'SET_DEPTH'; payload: number }
  | { type: 'FOCUS_ON_NODE'; payload: string }
  | { type: 'ADD_FILTER'; payload: Record<string, any> }
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: ViewState }
  | { type: 'FETCH_ERROR'; payload: string }
  | { type: 'SET_INITIAL_ROOTS'; payload: string[] };

// ====================================================================================
// Action Creators - Functions to create and dispatch actions consistently.
// ====================================================================================

/** Creates an action to change the analysis depth in the query. */
export const setDepth = (depth: number): Action => ({ type: 'SET_DEPTH', payload: depth });

/** Creates an action to change the query's root node, focusing the view. */
export const focusOnNode = (fqn: string): Action => ({ type: 'FOCUS_ON_NODE', payload: fqn });

/** Creates an action to signal the start of a data fetch. */
export const fetchStart = (): Action => ({ type: 'FETCH_START' });

/** Creates an action to handle a successful data fetch, providing the new view state. */
export const fetchSuccess = (view: ViewState): Action => ({ type: 'FETCH_SUCCESS', payload: view });

/** Creates an action to handle a failed data fetch, providing an error message. */
export const fetchError = (error: string): Action => ({ type: 'FETCH_ERROR', payload: error });

/** Creates an action to set the initial root FQNs after fetching project info. */
export const setInitialRoots = (rootFqns: string[]): Action => ({
  type: 'SET_INITIAL_ROOTS',
  payload: rootFqns,
});