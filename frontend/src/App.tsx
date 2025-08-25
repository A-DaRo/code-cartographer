import React, { useContext, useEffect } from 'react';
import { AppContext } from './state/AppContext';
import { executeQuery } from './api/client';
import { fetchStart, fetchSuccess, fetchError } from './state/actions';
import { GraphView } from './components/GraphView';

/**
 * The root component that orchestrates the entire application, including
 * the side effect hook that connects state changes to API calls.
 */
function App() {
  const { state, dispatch } = useContext(AppContext);

  // This crucial hook runs whenever the 'query' part of the state changes.
  // It is responsible for triggering a new backend request.
  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async () => {
      dispatch(fetchStart());
      try {
        const newViewState = await executeQuery(state.query, abortController.signal);
        dispatch(fetchSuccess(newViewState));
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          dispatch(fetchError(error.message || 'An unknown error occurred.'));
        }
      }
    };

    fetchData();

    // Cleanup function: This is critical for cancelling stale in-flight requests
    return () => {
      abortController.abort();
    };
  }, [state.query, dispatch]);

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '1rem', backgroundColor: '#f0f0f0', borderBottom: '1px solid #ddd' }}>
        <h1>Code Cartographer</h1>
        {state.isLoading && <span>Loading...</span>}
        {state.error && <span style={{ color: 'red' }}>Error: {state.error}</span>}
      </header>
      <main style={{ flex: 1 }}>
        <GraphView />
      </main>
    </div>
  );
}

export default App;