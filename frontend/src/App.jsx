import { useState } from 'react'
import axios from 'axios'
import {
  AlertCircle,
  ArrowUpRight,
  Eye,
  Loader2,
  Newspaper,
  Radar,
  Scale,
  Search,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react'
import './index.css'

const apiUrl =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '/api' : 'http://localhost:5000')

const sampleClaim =
  'Paste a claim, headline, or paragraph. TruthLens will scan live coverage, weigh trusted sources, and show whether reporting supports or disputes it.'

function verdictMeta(verdict) {
  if (verdict === 'Likely supported') {
    return {
      tone: 'support',
      title: 'Coverage Supports The Claim',
      icon: <ShieldCheck size={60} color="#34d399" strokeWidth={1.5} />,
    }
  }

  if (verdict === 'Likely disputed') {
    return {
      tone: 'oppose',
      title: 'Coverage Pushes Back On The Claim',
      icon: <ShieldAlert size={60} color="#fb7185" strokeWidth={1.5} />,
    }
  }

  return {
    tone: 'mixed',
    title: verdict,
    icon: <Scale size={60} color="#fbbf24" strokeWidth={1.5} />,
  }
}

function App() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!text.trim()) {
      setError('Paste a claim or article text before scanning.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${apiUrl}/predict`, { text })
      setResult(response.data)
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.error || 'Unable to analyze the claim right now.')
    } finally {
      setLoading(false)
    }
  }

  const evidence = result?.evidence
  const totalEvidence =
    (evidence?.support || 0) + (evidence?.oppose || 0) + (evidence?.mixed || 0)
  const supportPercent = totalEvidence ? ((evidence.support / totalEvidence) * 100).toFixed(0) : 0
  const opposePercent = totalEvidence ? ((evidence.oppose / totalEvidence) * 100).toFixed(0) : 0
  const mixedPercent = totalEvidence ? ((evidence.mixed / totalEvidence) * 100).toFixed(0) : 0

  const meta = result ? verdictMeta(result.verdict) : null

  return (
    <>
      <div className="bg-orb bg-orb-1"></div>
      <div className="bg-orb bg-orb-2"></div>

      <div className="app-shell">
        <div className="hero-panel">
          <div className="hero-copy">
            <div className="eyebrow">
              <Radar size={16} />
              <span>Live Evidence Engine</span>
            </div>
            <h1>TruthLens</h1>
            <p>
              Paste any news claim and get an evidence-first verdict built from live
              coverage, credibility weighting, and contradiction signals.
            </p>
          </div>

          <div className="hero-card">
            <div className="hero-card-icon">
              <Eye size={28} color="#7dd3fc" strokeWidth={1.7} />
            </div>
            <h2>What it does</h2>
            <ul className="feature-list">
              <li>Searches live reporting around the claim</li>
              <li>Counts supporting, opposing, and mixed coverage</li>
              <li>Weights stronger outlets higher than random reposts</li>
              <li>Falls back to the local classifier if live evidence is thin</li>
            </ul>
          </div>
        </div>

        <div className="workspace-panel">
          <div className="glass-card">
            <form onSubmit={handleSubmit} className="analysis-form">
              <label className="textarea-label" htmlFor="claim-input">
                Claim to verify
              </label>
              <div className="input-group">
                <textarea
                  id="claim-input"
                  placeholder={sampleClaim}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  disabled={loading}
                />
              </div>

              <button type="submit" className="submit-btn" disabled={loading || !text.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="spinner" size={22} />
                    <span>Scanning live coverage...</span>
                  </>
                ) : (
                  <>
                    <Search size={20} strokeWidth={2.5} />
                    <span>Analyze Claim</span>
                  </>
                )}
              </button>
            </form>

            {error && (
              <div className="error-message">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            {result && meta && (
              <section className={`result-panel ${meta.tone}`}>
                <div className="result-topline">
                  <div className="result-icon-wrapper">{meta.icon}</div>
                  <div className="result-heading">
                    <span className="status-pill">{result.verdict}</span>
                    <h2>{meta.title}</h2>
                    <p>{result.summary}</p>
                  </div>
                </div>

                <div className="metric-grid">
                  <article className="metric-card">
                    <span className="metric-label">Verdict confidence</span>
                    <strong>{result.confidence.toFixed(1)}%</strong>
                    <div className="meter">
                      <div className="meter-fill confidence" style={{ width: `${result.confidence}%` }} />
                    </div>
                  </article>

                  <article className="metric-card">
                    <span className="metric-label">Supporting sources</span>
                    <strong>{evidence.support}</strong>
                    <span className="metric-subtle">{supportPercent}% of relevant coverage</span>
                  </article>

                  <article className="metric-card">
                    <span className="metric-label">Opposing sources</span>
                    <strong>{evidence.oppose}</strong>
                    <span className="metric-subtle">{opposePercent}% of relevant coverage</span>
                  </article>

                  <article className="metric-card">
                    <span className="metric-label">Mixed coverage</span>
                    <strong>{evidence.mixed}</strong>
                    <span className="metric-subtle">{mixedPercent}% of relevant coverage</span>
                  </article>
                </div>

                <div className="analysis-split">
                  <div className="claim-card">
                    <span className="section-label">Analyzed claim</span>
                    <p>{result.claim}</p>
                    <div className="query-list">
                      {result.queries?.map((query) => (
                        <span key={query} className="query-pill">
                          {query}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="claim-card compact">
                    <span className="section-label">Model fallback</span>
                    {result.modelSignal ? (
                      <>
                        <div className="signal-row">
                          <span>Classifier vote</span>
                          <strong>{result.modelSignal.label}</strong>
                        </div>
                        <div className="signal-row">
                          <span>Classifier confidence</span>
                          <strong>{result.modelSignal.confidence.toFixed(1)}%</strong>
                        </div>
                      </>
                    ) : (
                      <p>Local classifier is unavailable, so the verdict is based only on live evidence.</p>
                    )}
                    {result.fallbackUsed && (
                      <p className="fallback-note">
                        Live search returned limited results, so this answer leans more on fallback scoring.
                      </p>
                    )}
                  </div>
                </div>

                <div className="sources-header">
                  <div>
                    <span className="section-label">Evidence sources</span>
                    <h3>Where the verdict came from</h3>
                  </div>
                  <div className="source-meta">
                    <Newspaper size={16} />
                    <span>{result.sources.length} sources surfaced</span>
                  </div>
                </div>

                <div className="sources-grid">
                  {result.sources.map((source) => (
                    <article key={`${source.link}-${source.title}`} className={`source-card ${source.stance}`}>
                      <div className="source-card-top">
                        <span className={`stance-badge ${source.stance}`}>{source.stance}</span>
                        <span className="strength-badge">{source.strength.toFixed(0)}% strength</span>
                      </div>

                      <h4>{source.title}</h4>
                      <p>{source.snippet || 'Snippet unavailable for this source.'}</p>

                      <div className="source-footer">
                        <div>
                          <span className="source-name">{source.source}</span>
                          <span className="source-date">{source.publishedAt}</span>
                        </div>
                        <a href={source.link} target="_blank" rel="noreferrer">
                          Open
                          <ArrowUpRight size={16} />
                        </a>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

export default App
