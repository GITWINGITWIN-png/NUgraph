import { useState } from 'react'

export default function SearchBar({ facets, onSearch }) {
  const [q, setQ] = useState('')
  const [language, setLanguage] = useState('')
  const [genre, setGenre] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (q.trim()) onSearch(q.trim(), { language: language || undefined, genre: genre || undefined })
  }

  return (
    <form className="searchbar" onSubmit={submit}>
      <input
        autoFocus
        placeholder="Describe a novel…  e.g. villainess reincarnated into an otome game"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="filters">
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="">any language</option>
          {facets?.languages?.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={genre} onChange={(e) => setGenre(e.target.value)}>
          <option value="">any genre</option>
          {facets?.genres?.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
        <button type="submit">Search</button>
      </div>
    </form>
  )
}
