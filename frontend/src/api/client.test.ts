import { describe, it, expect, vi, afterEach } from 'vitest';
import { executeQuery, Query } from './client';

describe('api/client', () => {
  // Restore any spies after each test to ensure test isolation
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('executeQuery should return a ViewState on a successful request', async () => {
    const query: Query = { root_fqns: ['my_app'], depth: 1, filter_rules: [] };
    const result = await executeQuery(query, new AbortController().signal);
    expect(result.nodes[0].fqn).toBe('my_app');
  });

  it('executeQuery should throw an error on a failed request', async () => {
    const errorQuery: Query = { root_fqns: ['error.trigger'], depth: 1, filter_rules: [] };
    await expect(executeQuery(errorQuery, new AbortController().signal)).rejects.toThrow(
      'API Error: 500 Internal Server Error - {"message":"Internal Server Error"}'
    );
  });
  
  it('executeQuery should pass the AbortSignal to fetch', () => {
    // **FIX**: Spy on the global fetch to reliably test the signal passing.
    const fetchSpy = vi.spyOn(global, 'fetch');
    const abortController = new AbortController();
    const query: Query = { root_fqns: ['my_app'], depth: 1, filter_rules: [] };
    
    // We don't need to await or catch, just call the function.
    executeQuery(query, abortController.signal).catch(() => {});

    // Assert that fetch was called with an options object containing our signal.
    expect(fetchSpy).toHaveBeenCalledOnce();
    const fetchOptions = fetchSpy.mock.calls[0][1];
    expect(fetchOptions?.signal).toBe(abortController.signal);
  });
});