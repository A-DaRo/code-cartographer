import React, { useContext, useEffect } from 'react';
import { AppContext } from './state/AppContext';
import { executeQuery } from './api/client';
import { fetchStart, fetchSuccess, fetchError } from './state/actions';
import { GraphView } from './components/GraphView';
import { Controls } from './components/Controls';

function App() {
  const { state, dispatch } = useContext(AppContext);

  // **FIX**: This single useEffect hook handles both the initial data load
  // and all subsequent updates when the query state changes. This is the
  // canonical and most robust approach.
  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async () => {
      dispatch(fetchStart());
      try {
        // This will send the default query on initial mount, and the
        // updated query on subsequent changes.
        const newViewState = await executeQuery(state.query, abortController.signal);
        dispatch(fetchSuccess(newViewState));
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          dispatch(fetchError(error.message || 'An unknown error occurred.'));
        }
      }
    };

    fetchData();

    // The cleanup function cancels the in-flight request if state.query
    // changes again before the current request is complete.
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