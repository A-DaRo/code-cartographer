// src/state/actions.ts
import { ViewState } from '../api/client';

export type Action =
  | { type: 'SET_DEPTH'; payload: number }
  | { type: 'FOCUS_ON_NODE'; payload: string }
  | { type: 'ADD_FILTER'; payload: Record<string, any> }
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: ViewState }
  | { type: 'FETCH_ERROR'; payload: string };

// Action Creators (for convenience)
export const setDepth = (depth: number): Action => ({ type: 'SET_DEPTH', payload: depth });
export const focusOnNode = (fqn: string): Action => ({ type: 'FOCUS_ON_NODE', payload: fqn });
export const fetchStart = (): Action => ({ type: 'FETCH_START' });
export const fetchSuccess = (view: ViewState): Action => ({ type: 'FETCH_SUCCESS', payload: view });
export const fetchError = (error: string): Action => ({ type: 'FETCH_ERROR', payload: error });