import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react'; // Import fireEvent
import React from 'react';
import { Controls } from './Controls';
import { AppContext } from '../state/AppContext';
import { initialState, AppState } from '../state/reducer';
import { Action } from '../state/actions';

const renderWithContext = (
  ui: React.ReactElement,
  {
    providerProps,
  }: { providerProps: { state: AppState; dispatch: React.Dispatch<Action> } }
) => {
  return render(
    <AppContext.Provider value={providerProps}>{ui}</AppContext.Provider>
  );
};

describe('<Controls />', () => {
  it('should display the initial depth from the context state', () => {
    const mockState: AppState = {
      ...initialState,
      query: { ...initialState.query, depth: 5 },
    };
    const mockDispatch = vi.fn();

    renderWithContext(<Controls />, {
      providerProps: { state: mockState, dispatch: mockDispatch },
    });

    const slider = screen.getByLabelText('Traversal Depth');
    expect(slider).toHaveValue('5');
    expect(screen.getByText('Traversal Depth: 5')).toBeInTheDocument();
  });

  it('should dispatch a SET_DEPTH action when the slider is changed', async () => {
    const mockDispatch = vi.fn();
    renderWithContext(<Controls />, {
      providerProps: { state: initialState, dispatch: mockDispatch },
    });
    
    const slider = screen.getByLabelText('Traversal Depth');

    // **FIX**: Use fireEvent.change for reliable testing of range inputs.
    fireEvent.change(slider, { target: { value: '3' } });

    // THEN the dispatch function should have been called with the correct action
    expect(mockDispatch).toHaveBeenCalledWith({
      type: 'SET_DEPTH',
      payload: 3,
    });
  });
});