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
    root_fqns: [],
    depth: 1,
    filter_rules: [],
  },
  view: {
    nodes: [],
    edges: [],
  },
  isLoading: false,
  error: null,
};

export function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_DEPTH':
      // Only re-fetch if the depth actually changes
      if (state.query.depth === action.payload) {
        return state;
      }
      return {
        ...state,
        query: { ...state.query, depth: action.payload },
      };
      
    case 'FOCUS_ON_NODE':
      return {
        ...state,
        // Reset depth to 1 when focusing on a new node for a clean view
        query: { ...state.query, root_fqns: [action.payload], depth: 1 },
      };

    case 'SET_INITIAL_ROOTS':
      return {
        ...state,
        query: {
          ...state.query,
          root_fqns: action.payload, // This updates the state
        },
      };

    case 'FETCH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
      
    case 'FETCH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        view: action.payload,
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