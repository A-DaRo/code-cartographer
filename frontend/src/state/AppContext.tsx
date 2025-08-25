import React, { createContext, useReducer, Dispatch, ReactNode } from 'react';
import { appReducer, AppState, initialState } from './reducer';
import { Action } from './actions';

interface AppContextProps {
  state: AppState;
  dispatch: Dispatch<Action>;
}

export const AppContext = createContext<AppContextProps>({
  state: initialState,
  dispatch: () => null,
});

interface AppProviderProps {
  children: ReactNode;
}

/**
 * Provides the application state and dispatch function to the entire component tree.
 */
export const AppProvider = ({ children }: AppProviderProps) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};