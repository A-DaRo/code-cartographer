import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import App from './App';
import { AppProvider } from './state/AppContext';
import * as client from './api/client';

// Mock GraphView
vi.mock('./components/GraphView', () => ({
  GraphView: vi.fn(() => <div data-testid="graph-view-mock" />),
}));

describe('<App /> Integration Test', () => {
  beforeEach(() => {
    // Mock executeQuery with a small artificial delay
    vi.spyOn(client, 'executeQuery').mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                nodes: [
                  {
                    fqn: 'mock.fqn',
                    name: 'Mock Node',
                    element_type: 'class',
                    parent_fqn: null,
                  },
                ],
                edges: [],
              }),
            50
          )
        )
    );
  });

  it('should show a loading state on initial load and then render the graph', async () => {
    render(
      <AppProvider>
        <App />
      </AppProvider>
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
    expect(screen.getByTestId('graph-view-mock')).toBeInTheDocument();
  });

  it('should fetch new data when a user action changes the query', async () => {
    render(
      <AppProvider>
        <App />
      </AppProvider>
    );

    // Wait for the initial load to complete
    await waitFor(() => expect(screen.queryByText('Loading...')).not.toBeInTheDocument());

    const slider = await screen.findByLabelText(/Traversal Depth/);

    fireEvent.input(slider, { target: { value: '2' } });

    // THEN a loading state should reappear
    expect(await screen.findByText('Loading...')).toBeInTheDocument();

    // AND WHEN the second fetch completes, the loading state should disappear again
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });
});
