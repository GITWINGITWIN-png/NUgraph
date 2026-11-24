// Thin client for the NUgraph API. Paths are relative; Vite proxies /api -> :8001.

const asJson = (r) => {
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export const getFacets = () => fetch('/api/facets').then(asJson)

export const search = (q, { k = 12, language, genre } = {}) => {
  const p = new URLSearchParams({ q, k })
  if (language) p.set('language', language)
  if (genre) p.set('genre', genre)
  return fetch(`/api/search?${p}`).then(asJson)
}

export const getNovel = (id) => fetch(`/api/novel/${id}`).then(asJson)

export const getNeighbors = (id, { edgeTypes, limit = 40 } = {}) => {
  const p = new URLSearchParams({ limit })
  if (edgeTypes && edgeTypes.length) p.set('edge_types', edgeTypes.join(','))
  return fetch(`/api/graph/neighbors/${id}?${p}`).then(asJson)
}
