import { useEffect, useState } from 'react'
import SearchBar from './components/SearchBar'
import ResultList from './components/ResultList'
import GraphView, { EDGE_COLORS } from './components/GraphView'
import NovelPanel from './components/NovelPanel'
import * as api from './api'

const ALL_EDGES = ['RELATED', 'RECOMMENDS', 'SIMILAR', 'CO_LISTED', 'SAME_AUTHOR']

export default function App() {
  const [facets, setFacets] = useState(null)
  const [results, setResults] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [novel, setNovel] = useState(null)
  const [graph, setGraph] = useState(null)
  const [edgeTypes, setEdgeTypes] = useState(new Set(ALL_EDGES))
  const [loading, setLoading] = useState(false)

  useEffect(() => { api.getFacets().then(setFacets).catch(() => {}) }, [])

  const doSearch = async (q, opts) => {
    setLoading(true)
    try {
      const d = await api.search(q, opts)
      setResults(d.results)
    } finally {
      setLoading(false)
    }
  }

  const selectNovel = async (id) => {
    setSelectedId(id)
    const [n, g] = await Promise.all([
      api.getNovel(id),
      api.getNeighbors(id, { edgeTypes: [...edgeTypes] }),
    ])
    setNovel(n)
    setGraph(g)
  }

  // re-fetch the graph when the edge-type filter changes
  useEffect(() => {
    if (selectedId != null) api.getNeighbors(selectedId, { edgeTypes: [...edgeTypes] }).then(setGraph)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [edgeTypes])

  const toggleEdge = (t) =>
    setEdgeTypes((prev) => {
      const s = new Set(prev)
      s.has(t) ? s.delete(t) : s.add(t)
      return s
    })

  return (
    <div className="app">
      <header>
        <h1>NUgraph</h1>
        <span className="sub">relation graph &amp; search-by-description · 24,639 novels</span>
      </header>

      <div className="cols">
        <aside className="left">
          <SearchBar facets={facets} onSearch={doSearch} />
          {loading ? <p className="muted pad">searching…</p>
            : <ResultList results={results} onSelect={selectNovel} selectedId={selectedId} />}
        </aside>

        <main className="center">
          <div className="edgebar">
            {ALL_EDGES.map((t) => (
              <label key={t} className={'etoggle' + (edgeTypes.has(t) ? ' on' : '')}>
                <input type="checkbox" checked={edgeTypes.has(t)} onChange={() => toggleEdge(t)} />
                <span className="swatch" style={{ background: EDGE_COLORS[t] }} />
                {t}
              </label>
            ))}
          </div>
          {graph
            ? <GraphView data={graph} onSelectNode={selectNovel} />
            : <div className="placeholder">Search on the left, then pick a novel to explore its relations. Click any node to jump to it.</div>}
        </main>

        <aside className="right">
          <NovelPanel novel={novel} />
        </aside>
      </div>
    </div>
  )
}
