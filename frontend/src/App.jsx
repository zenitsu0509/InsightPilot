import { useState, useRef, useEffect } from 'react'
import './App.css'

const rawApiBase = import.meta.env.VITE_API_BASE_URL
const API_BASE_URL = (rawApiBase && rawApiBase.trim() ? rawApiBase.trim() : 'http://localhost:8000').replace(/\/$/, '')

const resolveApiUrl = (path = '') => {
  if (!path) return API_BASE_URL
  if (/^https?:\/\//i.test(path)) {
    return path
  }
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

const QUICK_PROMPTS = [
  'What were total sales by category?',
  'Compare revenue by region last quarter',
  'Show monthly sales trend for 2023',
  'Top products by revenue'
]

const DEFAULT_AGENT_MESSAGE = {
  type: 'agent',
  content: 'Hi! Ask me anything about your business data and I will generate SQL, visuals, and insights for you.'
}

function App() {
  const sessionIdRef = useRef(null)
  if (!sessionIdRef.current) {
    sessionIdRef.current = crypto?.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`
  }
  const sessionId = sessionIdRef.current

  const [messages, setMessages] = useState([DEFAULT_AGENT_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeResult, setActiveResult] = useState(null)
  const [error, setError] = useState(null)
  const [datasetCatalog, setDatasetCatalog] = useState([])
  const [catalogLoading, setCatalogLoading] = useState(false)
  const [tableName, setTableName] = useState('sales')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [clearing, setClearing] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const [datasetPreview, setDatasetPreview] = useState(null)

  const dataPreview = activeResult?.data ?? []
  const previewColumns = dataPreview.length ? Object.keys(dataPreview[0]) : []
  const previewRows = dataPreview.slice(0, 5)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (!inputRef.current) return
    const el = inputRef.current
    el.style.height = 'auto'
    const nextHeight = Math.min(el.scrollHeight, 160)
    el.style.height = `${nextHeight}px`
  }, [input])

  const fetchDatasetCatalog = async () => {
    setCatalogLoading(true)
    try {
      const res = await fetch(resolveApiUrl('/api/datasets'))
      const payload = await res.json()
      setDatasetCatalog(payload.tables || [])
    } catch (err) {
      console.error('Failed to fetch dataset catalog', err)
    } finally {
      setCatalogLoading(false)
    }
  }

  useEffect(() => {
    fetchDatasetCatalog()
  }, [])

  const sendQuery = async (question) => {
    const trimmed = question.trim()
    if (!trimmed) return

    const userMessage = { type: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(resolveApiUrl('/api/analyze'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: trimmed, session_id: sessionId })
      })

      const data = await response.json()

      if (!response.ok || data.error) {
        const message = data.error || 'Something went wrong.'
        setError(message)
        setMessages((prev) => [...prev, { type: 'agent', content: `⚠️ ${message}` }])
        return
      }

      const agentPayload = {
        type: 'agent',
        content: data.insights || 'Analysis complete.',
        sql: data.sql_query,
        visualization: data.visualization_url,
        chartSummary: data.visualization_summary,
        trendSummary: data.trend_analysis?.summary,
        anomalySummary: data.anomaly_analysis?.summary,
        report: data.report_url
      }

      setMessages((prev) => [...prev, agentPayload])
      setActiveResult(data)
    } catch (err) {
      const fallback = `Network error: ${err.message}`
      setError(fallback)
      setMessages((prev) => [...prev, { type: 'agent', content: fallback }])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (loading) return
    sendQuery(input)
  }

  const handlePromptClick = (prompt) => {
    if (loading) return
    setInput(prompt)
    sendQuery(prompt)
  }

  const handleDatasetUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file || uploading) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('table_name', tableName || 'sales')

    setUploading(true)
    setUploadError(null)

    try {
      const response = await fetch(resolveApiUrl('/api/upload-csv'), {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Upload failed')
      }

      if (data.preview) {
        setDatasetPreview({
          table: data.table,
          columns: data.columns,
          rows: data.preview
        })
        setActiveResult(null)
      }

      fetchDatasetCatalog()
    } catch (err) {
      setUploadError(err.message)
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleClearChat = async () => {
    if (loading || clearing) return

    setClearing(true)
    setMessages([DEFAULT_AGENT_MESSAGE])
    setActiveResult(null)
    setError(null)

    try {
      await fetch(resolveApiUrl('/api/session/reset'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })
    } catch (err) {
      console.error('Failed to reset session', err)
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>InsightPilot</h1>
        </div>

        <div className="sidebar-section">
          <h3>Dataset Control</h3>
          <div className="dataset-control">
            <div className="input-group">
              <label>Target Table</label>
              <input
                type="text"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                placeholder="sales"
              />
            </div>
            
            <label className="upload-label">
              {uploading ? 'Uploading...' : 'Click to Upload CSV'}
              <input type="file" accept=".csv" onChange={handleDatasetUpload} disabled={uploading} />
            </label>
            {uploadError && <p className="error-text">{uploadError}</p>}

            <button className="btn-secondary" onClick={fetchDatasetCatalog} disabled={catalogLoading}>
              {catalogLoading ? 'Refreshing...' : 'Refresh Catalog'}
            </button>
          </div>
        </div>

        <div className="sidebar-section">
          <h3>Available Tables</h3>
          <ul className="dataset-list">
            {datasetCatalog.length === 0 ? (
              <li className="dataset-item">No tables found</li>
            ) : (
              datasetCatalog.map((table) => (
                <li key={table.table} className="dataset-item">
                  <strong>{table.table}</strong>
                  <span>{table.rows?.toLocaleString()} rows</span>
                </li>
              ))
            )}
          </ul>
        </div>
      </aside>

      <main className="main-content">
        <section className="chat-section">
          <header className="chat-header">
            <div className="status-indicator">
              <span className={`dot ${loading ? 'busy' : ''}`}></span>
              {loading ? 'Agent is thinking...' : 'Agent is ready'}
            </div>
            <button 
              className="btn-secondary" 
              onClick={handleClearChat}
              disabled={loading || clearing || messages.length <= 1}
            >
              {clearing ? 'Clearing...' : 'Clear Chat'}
            </button>
          </header>

          <div className="messages-container">
            {messages.length === 1 ? (
              <div className="welcome-screen">
                <h2>Autonomous Data Analyst</h2>
                <p>Ask natural-language questions about your warehouse. The agent will plan the query, validate results, draw charts, and package everything in a PDF.</p>
                <div className="quick-prompts">
                  {QUICK_PROMPTS.map((prompt) => (
                    <button key={prompt} className="prompt-card" onClick={() => handlePromptClick(prompt)}>
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className={`message ${msg.type}`}>
                  <div className="avatar">
                    {msg.type === 'agent' ? '🤖' : '👤'}
                  </div>
                  <div className="message-content">
                    <p>{msg.content}</p>
                    {msg.sql && (
                      <div className="sql-snippet">
                        <code>{msg.sql}</code>
                      </div>
                    )}
                    {(msg.trendSummary || msg.anomalySummary) && (
                      <div className="diagnostic-chips">
                        {msg.trendSummary && <span className="badge">Trend: {msg.trendSummary}</span>}
                        {msg.anomalySummary && <span className="badge">Anomaly: {msg.anomalySummary}</span>}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <form className="input-wrapper" onSubmit={handleSubmit}>
              <div className="input-shell">
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      if (!loading) {
                        sendQuery(input)
                      }
                    }
                  }}
                  placeholder="Ask anything about your data..."
                  disabled={loading}
                />
                <button type="submit" className="send-btn" disabled={loading}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 2L11 13"></path>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                  </svg>
                </button>
              </div>
            </form>
          </div>
        </section>

        <section className="results-section">
          <div className="results-header">
            <h2>Analysis Results</h2>
          </div>
          <div className="results-content">
            {datasetPreview && !activeResult && (
              <div className="result-card">
                <div className="card-header">
                  <span>Uploaded Data Preview: {datasetPreview.table}</span>
                </div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        {datasetPreview.columns.map(col => <th key={col}>{col}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {datasetPreview.rows.map((row, i) => (
                        <tr key={i}>
                          {datasetPreview.columns.map(col => <td key={col}>{row[col]}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeResult ? (
              <>
                <div className="result-card">
                  <div className="card-header">
                    <span>Insight</span>
                  </div>
                  <p>{activeResult.insights}</p>
                </div>

                {activeResult.visualization_url && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Visualization</span>
                    </div>
                    <div className="viz-container">
                      <img src={resolveApiUrl(activeResult.visualization_url)} alt="Visualization" />
                    </div>
                  </div>
                )}

                {activeResult.trend_analysis && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Trend Analysis</span>
                      <span className="badge">Diagnostic</span>
                    </div>
                    <p>{activeResult.trend_analysis.summary}</p>
                    <div className="trend-grid">
                      <div>
                        <span>Start</span>
                        <strong>{Number.isFinite(activeResult.trend_analysis.start) ? activeResult.trend_analysis.start.toFixed(2) : '-'}</strong>
                      </div>
                      <div>
                        <span>End</span>
                        <strong>{Number.isFinite(activeResult.trend_analysis.end) ? activeResult.trend_analysis.end.toFixed(2) : '-'}</strong>
                      </div>
                      <div>
                        <span>Change</span>
                        <strong>{activeResult.trend_analysis.change_pct?.toFixed(1)}%</strong>
                      </div>
                    </div>
                  </div>
                )}

                {activeResult.anomaly_analysis && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Anomalies</span>
                      <span className="badge">Diagnostic</span>
                    </div>
                    <p>{activeResult.anomaly_analysis.summary}</p>
                    <ul className="anomaly-list">
                      {activeResult.anomaly_analysis.anomalies?.slice(0, 3).map((a, i) => (
                        <li key={i}>
                          <span>{a.period}</span>
                          <strong>z={a.z_score?.toFixed(2)}</strong>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {activeResult.forecast_analysis && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Forecast</span>
                      <span className="badge">Predictive</span>
                    </div>
                    <p>{activeResult.forecast_analysis.summary}</p>
                    {activeResult.forecast_analysis.method && (
                      <div style={{marginTop: '0.5rem', fontSize: '0.85rem', color: '#8899aa'}}>
                        Method: {activeResult.forecast_analysis.method}
                      </div>
                    )}
                    {activeResult.forecast_analysis.forecasts && (
                      <div className="table-container" style={{marginTop: '1rem'}}>
                        <table>
                          <thead>
                            <tr>
                              <th>Period</th>
                              <th>Forecast</th>
                              <th>Lower Bound</th>
                              <th>Upper Bound</th>
                            </tr>
                          </thead>
                          <tbody>
                            {activeResult.forecast_analysis.forecasts.map((f, i) => (
                              <tr key={i}>
                                <td>{f.period}</td>
                                <td>{Number.isFinite(f.value) ? f.value.toFixed(2) : '-'}</td>
                                <td>{Number.isFinite(f.lower_bound) ? f.lower_bound.toFixed(2) : '-'}</td>
                                <td>{Number.isFinite(f.upper_bound) ? f.upper_bound.toFixed(2) : '-'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}

                {activeResult.statistical_tests && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Statistical Tests</span>
                      <span className="badge">Diagnostic</span>
                    </div>
                    <p>{activeResult.statistical_tests.summary}</p>
                    <div style={{marginTop: '1rem'}}>
                      {activeResult.statistical_tests.tests && Object.entries(activeResult.statistical_tests.tests).map(([testName, testData]) => (
                        <div key={testName} style={{marginBottom: '1rem', padding: '0.75rem', background: '#1e2430', borderRadius: '6px'}}>
                          <div style={{fontWeight: '600', marginBottom: '0.5rem', textTransform: 'capitalize'}}>
                            {testName.replace(/_/g, ' ')}
                          </div>
                          <div style={{fontSize: '0.9rem', color: '#8899aa'}}>
                            {testData.summary || testData.test || '-'}
                          </div>
                          {testData.p_value !== undefined && (
                            <div style={{marginTop: '0.5rem', fontSize: '0.85rem'}}>
                              <span style={{color: '#8899aa'}}>p-value: </span>
                              <span style={{fontFamily: 'monospace', color: testData.significant || testData.is_stationary === false ? '#ff6b6b' : '#51cf66'}}>
                                {Number.isFinite(testData.p_value) ? testData.p_value.toFixed(4) : '-'}
                              </span>
                              {testData.significant !== undefined && (
                                <span style={{marginLeft: '0.75rem', color: testData.significant ? '#ff6b6b' : '#51cf66'}}>
                                  {testData.significant ? '✓ Significant' : '○ Not Significant'}
                                </span>
                              )}
                              {testData.is_stationary !== undefined && (
                                <span style={{marginLeft: '0.75rem', color: testData.is_stationary ? '#51cf66' : '#ff6b6b'}}>
                                  {testData.is_stationary ? '✓ Stationary' : '○ Non-Stationary'}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {previewColumns.length > 0 && (
                  <div className="result-card">
                    <div className="card-header">
                      <span>Data Preview</span>
                    </div>
                    <div className="table-container">
                      <table>
                        <thead>
                          <tr>
                            {previewColumns.map(col => <th key={col}>{col}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {previewRows.map((row, i) => (
                            <tr key={i}>
                              {previewColumns.map(col => <td key={col}>{row[col]}</td>)}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {activeResult.report_url && (
                  <a href={resolveApiUrl(activeResult.report_url)} target="_blank" rel="noreferrer" className="download-btn">
                    Download PDF Report
                  </a>
                )}
              </>
            ) : (
              <div className="empty-state-results">
                <p>Run a query to see detailed analysis, charts, and data previews here.</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
