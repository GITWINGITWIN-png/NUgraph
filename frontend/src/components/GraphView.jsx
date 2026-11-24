import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'

export const EDGE_COLORS = {
  RELATED: '#e6194B',
  RECOMMENDS: '#4363d8',
  SAME_AUTHOR: '#3cb44b',
  CO_LISTED: '#f58231',
  SIMILAR: '#911eb4',
}

export default function GraphView({ data, onSelectNode }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !data) return

    const elements = [
      ...data.nodes.map((n) => ({
        data: { id: String(n.id), label: n.name, center: n.center ? 1 : 0 },
      })),
      ...data.edges.map((e, i) => ({
        data: { id: `e${i}`, source: String(e.source), target: String(e.target), type: e.type },
      })),
    ]

    const cy = cytoscape({
      container: ref.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'font-size': 8,
            width: 18,
            height: 18,
            'background-color': '#9ca3af',
            color: '#1f2937',
            'text-wrap': 'ellipsis',
            'text-max-width': 90,
            'text-valign': 'bottom',
            'text-margin-y': 2,
          },
        },
        {
          selector: 'node[center = 1]',
          style: {
            'background-color': '#111827',
            width: 30,
            height: 30,
            'font-size': 11,
            'font-weight': 'bold',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'curve-style': 'bezier',
            opacity: 0.7,
            'line-color': (e) => EDGE_COLORS[e.data('type')] || '#999',
          },
        },
      ],
      layout: {
        name: 'concentric',
        concentric: (n) => (n.data('center') ? 10 : 1),
        levelWidth: () => 1,
        minNodeSpacing: 35,
      },
    })

    cy.on('tap', 'node', (evt) => onSelectNode(Number(evt.target.id())))

    return () => cy.destroy()
  }, [data, onSelectNode])

  return <div ref={ref} className="graph" />
}
