// src/state/reducer.ts
import { Query, ViewState } from '../api/client';
import { Action } from './actions';

export interface AppState {
  query: Query;
  view: ViewState;
  isLoading: boolean;
  error: string | null;
}

export const initialState: AppState = {
  query: {
    root_fqns: [], // Initially empty, will be populated on first load
    depth: 1,
    filter_rules: [],
  },
  view: {
    nodes: [],
    edges: [],
  },
  isLoading: true, // Start in loading state
  error: null,
};

/**
 * A pure function that calculates state changes. Given the current state and an
 * action, it must return a new state object without mutating the original.
 * @param state - The current application state.
 * @param action - The action to be processed.
 * @returns A new application state.
 */
export function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_DEPTH':
      return {
        ...state,
        query: { ...state.query, depth: action.payload },
      };
    case 'FOCUS_ON_NODE':
      // When focusing, we reset the query to be centered on the new node
      return {
        ...state,
        query: { ...state.query, root_fqns: [action.payload], depth: 1 },
      };
    case 'FETCH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'FETCH_SUCCESS':
      // If this is the very first load, set the root FQN
      const newQuery = state.query.root_fqns.length === 0 && action.payload.nodes.length > 0
        ? { ...state.query, root_fqns: [action.payload.nodes[0].fqn] }
        : state.query;

      return {
        ...state,
        isLoading: false,
        view: action.payload,
        query: newQuery,
      };
    case 'FETCH_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
      };
    default:
      return state;
  }
}