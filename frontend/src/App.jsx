import { useState, useRef, useEffect } from 'react'
import './App.css'

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
  const [datasetInfo, setDatasetInfo] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [clearing, setClearing] = useState(false)
  const messagesEndRef = useRef(null)

  const dataPreview = activeResult?.data ?? []
  const previewColumns = dataPreview.length ? Object.keys(dataPreview[0]) : []
  const previewRows = dataPreview.slice(0, 5)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendQuery = async (question) => {
    const trimmed = question.trim()
    if (!trimmed) return

    const userMessage = { type: 'user', content: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
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
    formData.append('table_name', 'sales')

    setUploading(true)
    setUploadError(null)

    try {
      const response = await fetch('http://localhost:8000/api/upload-csv', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Upload failed')
      }

      setDatasetInfo({
        filename: file.name,
        rows: data.rows,
        columns: data.columns,
        encoding: data.encoding,
        table: data.table,
        updatedAt: new Date().toISOString()
      })
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
      await fetch('http://localhost:8000/api/session/reset', {
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
      <header className="hero">
        <p className="eyebrow">Autonomous Data Analyst</p>
        <h1>Insights, SQL, and Reports in seconds</h1>
        <p className="subtitle">
          Ask natural-language questions about your warehouse. The agent will plan the query, validate results, draw charts, and package everything in a PDF.
        </p>
        <div className="prompt-chips">
          {QUICK_PROMPTS.map((prompt) => (
            <button key={prompt} className="chip" onClick={() => handlePromptClick(prompt)} disabled={loading}>
              {prompt}
            </button>
          ))}
        </div>

        <div className="dataset-panel">
          <div>
            <h3>Dataset Control</h3>
            <p>Upload a CSV to refresh the `sales` table the agent queries.</p>
            {datasetInfo ? (
              <div className="dataset-meta">
                <span>{datasetInfo.filename}</span>
                <span>{datasetInfo.rows.toLocaleString()} rows · {datasetInfo.columns.length} columns</span>
                <span>Encoding: {datasetInfo.encoding}</span>
              </div>
            ) : (
              <span className="dataset-placeholder">No custom dataset uploaded yet.</span>
            )}
          </div>
          <label className={`upload-button ${uploading ? 'disabled' : ''}`}>
            {uploading ? 'Uploading…' : 'Upload CSV'}
            <input type="file" accept=".csv" onChange={handleDatasetUpload} disabled={uploading} />
          </label>
        </div>
        {uploadError && <p className="error-text">{uploadError}</p>}
      </header>

      <main className="dashboard">
        <section className="panel chat-panel">
          <div className="panel-header">
            <div>
              <h2>Conversation</h2>
              <p>Collaborative analytics workspace</p>
            </div>
            <div className="panel-actions">
              <span className={`status-pill ${loading ? 'busy' : 'ready'}`}>
                {loading ? 'Analyzing' : 'Ready'}
              </span>
              <button
                type="button"
                className="clear-chat-button"
                onClick={handleClearChat}
                disabled={loading || clearing || messages.length <= 1}
              >
                {clearing ? 'Clearing…' : 'Clear chat'}
              </button>
            </div>
          </div>

          <div className="messages-area">
            {messages.map((msg, index) => (
              <div key={index} className={`bubble ${msg.type}`}>
                <p>{msg.content}</p>

                {msg.sql && (
                  <div className="sql-snippet">
                    <span>Generated SQL</span>
                    <code>{msg.sql}</code>
                  </div>
                )}

                {msg.visualization && (
                  <div className="viz-preview">
                    <img src={`http://localhost:8000${msg.visualization}`} alt="Visualization" />
                  </div>
                )}

                {msg.chartSummary && (
                  <p className="chart-summary">{msg.chartSummary}</p>
                )}

                {msg.report && (
                  <a className="report-chip" href={`http://localhost:8000${msg.report}`} target="_blank" rel="noreferrer">
                    Download PDF Report
                  </a>
                )}
              </div>
            ))}
            {loading && <div className="bubble agent">Thinking...</div>}
            <div ref={messagesEndRef} />
          </div>

          <form className="input-area" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your data lake..."
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Running' : 'Send'}
            </button>
          </form>

          {error && <p className="error-text">{error}</p>}
        </section>

        <section className="panel result-panel">
          <div className="panel-header">
            <div>
              <h2>Latest Analysis</h2>
              <p>SQL · Charts · PDF</p>
            </div>
          </div>

          <div className="result-body">
            {activeResult ? (
              <div className="result-stack">
                <div className="insight-card">
                  <p>{activeResult.insights || 'No insights generated yet.'}</p>
                </div>

                {activeResult.sql_query && (
                  <div className="meta-card">
                    <div className="meta-head">
                      <span>SQL used</span>
                      <span className="badge">auto-generated</span>
                    </div>
                    <code>{activeResult.sql_query}</code>
                  </div>
                )}

                {previewColumns.length > 0 && (
                  <div className="data-preview">
                    <div className="meta-head">
                      <span>Data preview</span>
                      <span>{`showing ${previewRows.length} of ${dataPreview.length}`}</span>
                    </div>
                    <div className="table-wrapper">
                      <table>
                        <thead>
                          <tr>
                            {previewColumns.map((col) => (
                              <th key={col}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewRows.map((row, idx) => (
                            <tr key={idx}>
                              {previewColumns.map((col) => (
                                <td key={col}>{row[col]}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {activeResult.visualization_url && (
                  <div className="viz-card">
                    <div className="meta-head">
                      <span>Visualization</span>
                    </div>
                    <img src={`http://localhost:8000${activeResult.visualization_url}`} alt="Visualization" />
                    {activeResult.visualization_summary && (
                      <p className="chart-summary">{activeResult.visualization_summary}</p>
                    )}
                  </div>
                )}
                {!activeResult.visualization_url && activeResult.visualization_summary && (
                  <div className="insight-card">
                    <p>{activeResult.visualization_summary}</p>
                  </div>
                )}

                {activeResult.report_url && (
                  <a className="report-button" href={`http://localhost:8000${activeResult.report_url}`} target="_blank" rel="noreferrer">
                    Download PDF Report
                  </a>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <p>Run your first query to see auto-generated SQL, insights, and a PDF report.</p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
