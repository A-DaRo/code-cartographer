import React, { useContext } from 'react';
import { AppContext } from '../state/AppContext';
import { setDepth } from '../state/actions';

const controlPanelStyle: React.CSSProperties = {
  padding: '1rem',
  backgroundColor: '#f8f9fa',
  borderRight: '1px solid #dee2e6',
  minWidth: '250px',
  display: 'flex',
  flexDirection: 'column',
  gap: '1.5rem',
};

const controlGroupStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.5rem',
};

const labelStyle: React.CSSProperties = {
  fontWeight: 'bold',
  color: '#495057',
};

/**
 * A UI component that provides controls for manipulating the graph query.
 * It reads the current query state from the AppContext and dispatches
 * actions to update it based on user interaction.
 */
export const Controls = () => {
  const { state, dispatch } = useContext(AppContext);

  const handleDepthChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newDepth = parseInt(event.target.value, 10);
    dispatch(setDepth(newDepth));
  };

  return (
    <aside style={controlPanelStyle}>
      <h2>Controls</h2>
      <div style={controlGroupStyle}>
        <label htmlFor="depth-slider" style={labelStyle}>
          Traversal Depth: {state.query.depth}
        </label>
        <input
          id="depth-slider"
          type="range"
          min="0"
          max="10"
          value={state.query.depth}
          onChange={handleDepthChange}
          aria-label="Traversal Depth"
        />
      </div>
      {/* Future controls like filters can be added here */}
    </aside>
  );
};