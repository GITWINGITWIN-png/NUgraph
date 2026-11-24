export default function NovelPanel({ novel }) {
  if (!novel) return <div className="panel muted">Select a novel to see its details.</div>
  return (
    <div className="panel">
      <h2>{novel.name}</h2>
      <div className="meta">
        <span>{novel.original_language}</span>
        <span>★ {novel.rating ?? '–'}</span>
        <span>{novel.novel_type}</span>
      </div>
      {novel.authors?.length ? <p className="muted">by {novel.authors.join(', ')}</p> : null}
      <p className="synopsis">
        {novel.synopsis || <em className="muted">Synopsis not scraped yet — using tags for now.</em>}
      </p>
      <div className="chips">
        {(novel.genres || []).map((g) => <span key={g} className="chip genre">{g}</span>)}
        {(novel.tags || []).slice(0, 12).map((t) => <span key={t} className="chip">{t}</span>)}
      </div>
      <a href={`https://www.novelupdates.com/?p=${novel.id}`} target="_blank" rel="noreferrer">
        View on NovelUpdates ↗
      </a>
    </div>
  )
}
