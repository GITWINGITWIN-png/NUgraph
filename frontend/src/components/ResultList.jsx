export default function ResultList({ results, onSelect, selectedId }) {
  if (!results.length) return <p className="muted pad">No results yet — try a search above.</p>
  return (
    <ul className="results">
      {results.map((r) => (
        <li
          key={r.id}
          className={r.id === selectedId ? 'sel' : ''}
          onClick={() => onSelect(r.id)}
          title={r.has_synopsis ? 'matched on synopsis' : 'matched on tags/genres (synopsis not scraped yet)'}
        >
          <span className="score">{r.score?.toFixed(2)}</span>
          <span className="title">{r.name}</span>
          <span className="lang">{r.language}{r.has_synopsis ? '' : ' ·t'}</span>
        </li>
      ))}
    </ul>
  )
}
