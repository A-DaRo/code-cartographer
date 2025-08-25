import { rest } from 'msw';
import { Query, ViewState } from '../api/client';

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const mockViewState: ViewState = {
  nodes: [
    { fqn: 'my_app', name: 'my_app', element_type: 'package', parent_fqn: null },
    { fqn: 'my_app.main', name: 'main', element_type: 'module', parent_fqn: 'my_app' },
    { fqn: 'my_app.main.App', name: 'App', element_type: 'class', parent_fqn: 'my_app.main' },
  ],
  edges: [
    { source_fqn: 'my_app.main.App', target_fqn: 'my_app.services.User', relationship_type: 'DEPENDENCY' }
  ]
};

export const handlers = [
  rest.post(`${API_URL}/api/v1/query`, async (req, res, ctx) => {
    // **FIX**: Introduce an artificial delay to simulate a real network request.
    // This gives asynchronous test utilities like findBy* a chance to
    // observe the intermediate loading states of the component.
    await ctx.delay(50); 
    
    const query = await req.json<Query>();
    
    if (query.root_fqns.includes('error.trigger')) {
      return res(ctx.status(500), ctx.json({ message: 'Internal Server Error' }));
    }
    
    if (query.root_fqns.includes('my_app.main.App')) {
      const focusedViewState: ViewState = {
         nodes: [
            { fqn: 'my_app.main.App', name: 'App', element_type: 'class', parent_fqn: 'my_app.main' },
            { fqn: 'my_app.services.User', name: 'User', element_type: 'class', parent_fqn: 'my_app.services' },
         ],
         edges: [
            { source_fqn: 'my_app.main.App', target_fqn: 'my_app.services.User', relationship_type: 'DEPENDENCY' }
         ]
      };
      return res(ctx.status(200), ctx.json(focusedViewState));
    }
    
    return res(ctx.status(200), ctx.json(mockViewState));
  }),
];