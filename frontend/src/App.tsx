import React, { useContext, useEffect, useRef } from 'react';
import { AppContext } from './state/AppContext';
import { ApiClient } from './api/client';
import { fetchStart, fetchSuccess, fetchError, setInitialRoots } from './state/actions';
import { GraphView } from './components/GraphView';
import { Controls } from './components/Controls';

function App() {
  const { state, dispatch } = useContext(AppContext);
  const hasFetchedInitialInfo = useRef(false);

  // Effect 1: Runs ONCE on mount to get the project info and set the first query.
  // This bootstraps the entire application.
  useEffect(() => {
    if (hasFetchedInitialInfo.current) return;
    hasFetchedInitialInfo.current = true;

    const fetchInitialInfo = async () => {
      try {
        const info = await ApiClient.getProjectInfo();
        // Dispatch the action to set the initial query roots.
        dispatch(setInitialRoots(info.root_fqns));
      } catch (error: any) {
        const errorMessage = error.message || 'Failed to load initial project info.';
        dispatch(fetchError(errorMessage));
      }
    };

    fetchInitialInfo();
  }, [dispatch]); // Dependency array ensures this effect runs only once.

  // Effect 2: Runs whenever the query state changes. This is triggered by the
  // bootstrap effect above, and then by any subsequent user interaction.
  useEffect(() => {
    // Guard: Don't run the query if the root_fqns are not yet populated.
    if (state.query.root_fqns.length === 0) {
      return;
    }

    const abortController = new AbortController();

    const fetchData = async () => {
      dispatch(fetchStart());
      try {
        const newViewState = await ApiClient.executeQuery(state.query, abortController.signal);
        dispatch(fetchSuccess(newViewState));
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          const errorMessage = error.message || 'An unknown error occurred while fetching data.';
          dispatch(fetchError(errorMessage));
        }
      }
    };

    fetchData();

    // Cleanup function: If the query changes again before this request is complete,
    // cancel the in-flight request.
    return () => {
      abortController.abort();
    };
  }, [state.query, dispatch]);

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '1rem', backgroundColor: '#f0f0f0', borderBottom: '1px solid #ddd', textAlign: 'center' }}>
        <h1>Code Cartographer</h1>
        {state.isLoading && <span>Loading...</span>}
        {state.error && <span style={{ color: 'red' }}>Error: {state.error}</span>}
      </header>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
        <Controls />
        <main style={{ flex: 1, position: 'relative' }}>
          <GraphView />
        </main>
      </div>
    </div>
  );
}

export default App;