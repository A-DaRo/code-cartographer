import React, { useEffect, useRef, useContext } from 'react';
import cytoscape from 'cytoscape';
import { AppContext } from '../state/AppContext';
import { focusOnNode } from '../state/actions';

/**
 * The main visualization component, responsible for rendering the graph using Cytoscape.js.
 */
export const GraphView = () => {
  const { state, dispatch } = useContext(AppContext);
  const cyContainerRef = useRef<HTMLDivElement>(null);
  const cyInstanceRef = useRef<cytoscape.Core | null>(null);

  // This effect runs only when state.view changes. Its job is to update
  // the Cytoscape instance to reflect the new ViewState.
  useEffect(() => {
    if (!cyContainerRef.current) return;

    const elements = [
      ...state.view.nodes.map(node => ({
        data: { id: node.fqn, label: node.name, type: node.element_type },
      })),
      ...state.view.edges.map(edge => ({
        data: {
          source: edge.source_fqn,
          target: edge.target_fqn,
          type: edge.relationship_type,
        },
      })),
    ];

    cyInstanceRef.current = cytoscape({
      container: cyContainerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'center',
            'color': '#000',
            'background-color': '#FFF',
            'border-width': 2,
            'border-color': '#CCC',
            'shape': 'round-rectangle',
          },
        },
        {
          selector: 'node[type="package"]',
          style: { 'background-color': '#E6F2FA', 'border-color': '#88BEE3' },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#ccc',
            'curve-style': 'bezier',
          },
        },
        {
          selector: 'edge[type="INHERITANCE"]',
          style: { 'target-arrow-shape': 'triangle', 'target-arrow-color': '#ccc', 'line-style': 'solid' },
        },
        {
          selector: 'edge[type="COMPOSITION"]',
          style: { 'source-arrow-shape': 'diamond', 'source-arrow-color': '#ccc', 'line-style': 'dashed' },
        },
        {
          selector: 'edge[type="DEPENDENCY"]',
          style: { 'target-arrow-shape': 'vee', 'target-arrow-color': '#ccc', 'line-style': 'dashed' },
        },
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        padding: 30,
      },
    });

    // --- Event Handlers ---
    cyInstanceRef.current.on('tap', 'node', (event) => {
      const fqn = event.target.id();
      dispatch(focusOnNode(fqn));
    });

    return () => {
      cyInstanceRef.current?.destroy();
    };
  }, [state.view, dispatch]);

  return <div ref={cyContainerRef} style={{ width: '100%', height: '100%' }} />;
};