import { describe, it, expect } from 'vitest';
import { appReducer, initialState } from './reducer';
import { focusOnNode, fetchStart, fetchSuccess, fetchError } from './actions';

describe('appReducer', () => {
  it('should handle FOCUS_ON_NODE action', () => {
    const action = focusOnNode('new.fqn');
    const newState = appReducer(initialState, action);
    expect(newState.query.root_fqns).toEqual(['new.fqn']);
    expect(newState.query.depth).toBe(1);
  });

  it('should handle FETCH_START action', () => {
    const stateWithError = { ...initialState, error: 'Old error' };
    const action = fetchStart();
    const newState = appReducer(stateWithError, action);
    expect(newState.isLoading).toBe(true);
    expect(newState.error).toBeNull();
  });

  it('should handle FETCH_SUCCESS action', () => {
    const viewState = { nodes: [{ fqn: 'a.b', name: 'b', element_type: 'class', parent_fqn: 'a' }], edges: [] };
    const action = fetchSuccess(viewState);
    const newState = appReducer(initialState, action);
    expect(newState.isLoading).toBe(false);
    expect(newState.view).toEqual(viewState);
    // It should set the initial root FQN on first success
    expect(newState.query.root_fqns).toEqual(['a.b']);
  });

  it('should handle FETCH_ERROR action', () => {
    const action = fetchError('Network failed');
    const newState = appReducer(initialState, action);
    expect(newState.isLoading).toBe(false);
    expect(newState.error).toBe('Network failed');
  });
});