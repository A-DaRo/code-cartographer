import { Query, ViewState } from '../api/client';
import { Action } from './actions';

export interface AppState {
  query: Query;
  view: ViewState;
  isLoading: boolean;
  error: string | null;
}

export const initialState: AppState = {
  // **FIX**: Start with a default root FQN to avoid the loop.
  // An empty query will fetch the top-level.
  query: {
    root_fqns: [],
    depth: 1,
    filter_rules: [],
  },
  view: {
    nodes: [],
    edges: [],
  },
  isLoading: false, // Start as not loading, the useEffect will trigger it.
  error: null,
};

export function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_DEPTH':
      return {
        ...state,
        query: { ...state.query, depth: action.payload },
      };
    case 'FOCUS_ON_NODE':
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
      // **FIX**: The re-fetch was caused by this logic. The useEffect hook
      // is a better place to handle the initial fetch. The reducer should
      // just handle the state update.
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