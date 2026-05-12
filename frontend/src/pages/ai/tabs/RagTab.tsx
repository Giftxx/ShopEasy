import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../../lib/api'
import type { Policy, PolicyDetail, PolicySearchResult } from '../../../types/api'

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORIES = ['refund', 'return', 'shipping', 'compensation', 'seller', 'general', 'other']

const CAT_COLOR: Record<string, string> = {
  refund: '#f97316',
  return: '#8b5cf6',
  shipping: '#10b981',
  compensation: '#f59e0b',
  seller: '#6366f1',
  general: '#64748b',
  other: '#94a3b8',
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function catColor(c: string | null) {
  return CAT_COLOR[c ?? ''] ?? '#64748b'
}

function fmtBytes(n: number | null | undefined): string {
  if (!n) return ''
  if (n < 1024) return `${n} B`
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1048576).toFixed(1)} MB`
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: '2-digit' })
}

function titleFromFilename(filename: string): string {
  const base = filename.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ')
  return base.charAt(0).toUpperCase() + base.slice(1)
}

// ── Types ─────────────────────────────────────────────────────────────────────

type UploadMode = 'file' | 'text'

// ── Component ─────────────────────────────────────────────────────────────────

export function RagTab() {
  // ── Policy list state ──────────────────────────────────────────────────────
  const [policies, setPolicies] = useState<Policy[]>([])
  const [listLoading, setListLoading] = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<PolicyDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  // ── Upload form state ──────────────────────────────────────────────────────
  const [showForm, setShowForm] = useState(false)
  const [mode, setMode] = useState<UploadMode>('file')
  const [formTitle, setFormTitle] = useState('')
  const [formCategory, setFormCategory] = useState('general')
  const [formVersion, setFormVersion] = useState('v1.0')
  const [formContent, setFormContent] = useState('')
  const [formFile, setFormFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [uploadDone, setUploadDone] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  // ── Search state ───────────────────────────────────────────────────────────
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<PolicySearchResult[]>([])
  const [searching, setSearching] = useState(false)

  // ── Data loading ───────────────────────────────────────────────────────────

  function loadPolicies() {
    setListLoading(true)
    api.getPolicies()
      .then(setPolicies)
      .catch(console.error)
      .finally(() => setListLoading(false))
  }

  useEffect(() => { loadPolicies() }, [])

  function toggleExpand(id: string) {
    if (expandedId === id) {
      setExpandedId(null)
      setDetail(null)
      return
    }
    setExpandedId(id)
    setDetail(null)
    setDetailLoading(true)
    api.getPolicyDetail(id)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setDetailLoading(false))
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm('Delete this policy? All chunks and the source file will be permanently removed.')) return
    setDeleting(id)
    try {
      await api.deletePolicy(id)
      if (expandedId === id) { setExpandedId(null); setDetail(null) }
      loadPolicies()
    } catch { /* silent */ }
    finally { setDeleting(null) }
  }

  async function handleDownload(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    setDownloading(id)
    try {
      const res = await api.downloadPolicyFile(id)
      const a = document.createElement('a')
      a.href = res.url
      a.download = res.filename
      a.target = '_blank'
      a.rel = 'noopener noreferrer'
      a.click()
    } catch {
      alert('Source file not found in storage.')
    } finally {
      setDownloading(null)
    }
  }

  // ── Drag-and-drop ──────────────────────────────────────────────────────────

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }, [])

  const onDragLeave = useCallback(() => setDragging(false), [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) {
      setFormFile(dropped)
      setFormTitle(prev => prev || titleFromFilename(dropped.name))
    }
  }, [])

  function pickFile(f: File) {
    setFormFile(f)
    setFormTitle(prev => prev || titleFromFilename(f.name))
  }

  // ── Form ───────────────────────────────────────────────────────────────────

  function resetForm() {
    setFormTitle('')
    setFormCategory('general')
    setFormVersion('v1.0')
    setFormContent('')
    setFormFile(null)
    setFormError(null)
    setUploadDone(false)
    if (fileRef.current) fileRef.current.value = ''
  }

  async function handleSubmit() {
    if (!formTitle.trim()) { setFormError('Policy title is required.'); return }
    if (mode === 'text' && !formContent.trim()) { setFormError('Content is required for text mode.'); return }
    if (mode === 'file' && !formFile) { setFormError('Please select or drop a file.'); return }
    setUploading(true)
    setFormError(null)
    setUploadDone(false)
    try {
      if (mode === 'text') {
        await api.createPolicy({
          title: formTitle.trim(),
          category: formCategory,
          version: formVersion.trim(),
          content: formContent.trim(),
        })
      } else {
        await api.uploadPolicyDocument(formFile!, formTitle.trim(), formCategory, formVersion.trim())
      }
      setUploadDone(true)
      resetForm()
      loadPolicies()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  // ── Search ─────────────────────────────────────────────────────────────────

  function handleSearch() {
    if (!searchQuery.trim()) return
    setSearching(true)
    setSearchResults([])
    api.searchPolicies(searchQuery.trim(), 10)
      .then(setSearchResults)
      .catch(console.error)
      .finally(() => setSearching(false))
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="rag-shell">

      {/* Header */}
      <div className="rag-header">
        <div>
          <h2 className="rag-header__title">Policy Documents</h2>
          <p className="rag-header__sub">
            Upload PDF / TXT / MD — AI extracts headings, auto-tags and chunks for RAG retrieval.
          </p>
        </div>
        <button
          type="button"
          className="rag-add-btn"
          onClick={() => { setShowForm(v => !v); if (uploadDone) setUploadDone(false) }}
        >
          {showForm ? 'Close' : '+ Add Policy'}
        </button>
      </div>

      {/* Upload form */}
      {showForm && (
        <div className="rag-form-card">
          <div className="rag-form-tabs">
            <button type="button" className={`rag-tab-btn${mode === 'file' ? ' is-active' : ''}`} onClick={() => setMode('file')}>
              Upload File
            </button>
            <button type="button" className={`rag-tab-btn${mode === 'text' ? ' is-active' : ''}`} onClick={() => setMode('text')}>
              Paste Text
            </button>
          </div>

          <div className="rag-form-fields">
            <div className="rag-field">
              <label>Policy Title *</label>
              <input value={formTitle} onChange={e => setFormTitle(e.target.value)} placeholder="e.g. Refund Policy" />
            </div>
            <div className="rag-field">
              <label>Category</label>
              <select value={formCategory} onChange={e => setFormCategory(e.target.value)}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="rag-field">
              <label>Version</label>
              <input value={formVersion} onChange={e => setFormVersion(e.target.value)} placeholder="v1.0" />
            </div>
          </div>

          {mode === 'file' ? (
            <>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.txt,.md"
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f) pickFile(f) }}
              />
              <div
                className={`rag-drop-zone${dragging ? ' is-dragging' : ''}${formFile ? ' has-file' : ''}`}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                onClick={() => fileRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
              >
                {formFile ? (
                  <div className="rag-drop-zone__file">
                    <span className="rag-drop-zone__file-icon">◩</span>
                    <div className="rag-drop-zone__file-info">
                      <strong>{formFile.name}</strong>
                      <span>{fmtBytes(formFile.size)}</span>
                    </div>
                    <button
                      type="button"
                      className="rag-drop-zone__clear"
                      onClick={e => { e.stopPropagation(); setFormFile(null); if (fileRef.current) fileRef.current.value = '' }}
                    >
                      &times;
                    </button>
                  </div>
                ) : (
                  <div className="rag-drop-zone__empty">
                    <span className="rag-drop-zone__upload-icon">&#9650;</span>
                    <strong>Drop file here or click to browse</strong>
                    <span>PDF, TXT, MD &mdash; max 50 MB</span>
                  </div>
                )}
              </div>
            </>
          ) : (
            <textarea
              className="rag-textarea"
              value={formContent}
              onChange={e => setFormContent(e.target.value)}
              placeholder="Paste policy content here..."
              rows={8}
            />
          )}

          {formError && <p className="rag-form-msg rag-form-msg--error">{formError}</p>}
          {uploadDone && <p className="rag-form-msg rag-form-msg--ok">Policy added and indexed successfully.</p>}

          <div className="rag-form-actions">
            <button type="button" className="rag-submit-btn" onClick={handleSubmit} disabled={uploading}>
              {uploading ? 'Processing...' : 'Save & Index'}
            </button>
            <button type="button" className="rag-cancel-btn" onClick={() => { setShowForm(false); resetForm() }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Policy list */}
      <div className="rag-list-card">
        <div className="rag-list-card__head">
          <span className="rag-list-card__title">Documents</span>
          <span className="rag-badge">{policies.length}</span>
        </div>

        {listLoading ? (
          <p className="rag-empty">Loading...</p>
        ) : policies.length === 0 ? (
          <p className="rag-empty">No policies yet. Click "+ Add Policy" to get started.</p>
        ) : (
          <div className="rag-table">
            <div className="rag-table__head">
              <span>Title</span>
              <span>Category</span>
              <span>Version</span>
              <span>Chunks</span>
              <span>Source File</span>
              <span>Updated</span>
              <span></span>
            </div>

            {policies.map(p => (
              <div key={p.id}>
                <div
                  className={`rag-table__row${expandedId === p.id ? ' is-expanded' : ''}`}
                  onClick={() => toggleExpand(p.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && toggleExpand(p.id)}
                >
                  <span className="rag-table__title">
                    <span className="rag-cat-dot" style={{ background: catColor(p.category) }} />
                    {p.title}
                  </span>
                  <span className="rag-table__cat">{p.category}</span>
                  <span className="rag-table__ver">{p.version}</span>
                  <span className="rag-table__chunks">{p.chunk_count}</span>
                  <span className="rag-table__file">
                    {p.source_filename
                      ? <span title={p.source_filename}>{p.source_filename} <em>{fmtBytes(p.file_size_bytes)}</em></span>
                      : <span className="rag-table__no-file">text only</span>
                    }
                  </span>
                  <span className="rag-table__date">{fmtDate(p.updated_at)}</span>
                  <span className="rag-table__actions" onClick={e => e.stopPropagation()} role="presentation">
                    {p.source_filename && (
                      <button
                        type="button"
                        className="rag-icon-btn rag-icon-btn--dl"
                        disabled={downloading === p.id}
                        onClick={e => handleDownload(p.id, e)}
                        title="Download source file"
                      >
                        {downloading === p.id ? '...' : 'Download'}
                      </button>
                    )}
                    <button
                      type="button"
                      className="rag-icon-btn rag-icon-btn--del"
                      disabled={deleting === p.id}
                      onClick={e => handleDelete(p.id, e)}
                      title="Delete policy"
                    >
                      {deleting === p.id ? '...' : 'Delete'}
                    </button>
                  </span>
                </div>

                {expandedId === p.id && (
                  <div className="rag-chunks">
                    {detailLoading && !detail ? (
                      <p className="rag-chunks__loading">Loading chunks...</p>
                    ) : detail ? (
                      <>
                        <div className="rag-chunks__meta">
                          <span>{detail.chunk_count} chunks</span>
                          {detail.source_filename && (
                            <span>{detail.source_filename} ({fmtBytes(detail.file_size_bytes)})</span>
                          )}
                          <span>Updated {fmtDate(detail.updated_at)}</span>
                        </div>
                        {detail.chunks.map(c => (
                          <div key={c.id} className="rag-chunk">
                            <div className="rag-chunk__header">
                              <span className="rag-chunk__idx">#{c.chunk_index}</span>
                              {c.heading && <span className="rag-chunk__heading">{c.heading}</span>}
                              {c.page_number != null && <span className="rag-chunk__page">p.{c.page_number}</span>}
                              {(c.tags ?? []).map(tag => (
                                <span key={tag} className="rag-chunk__tag" style={{ color: catColor(tag), background: `${catColor(tag)}20` }}>
                                  {tag}
                                </span>
                              ))}
                            </div>
                            <p className="rag-chunk__text">{c.chunk_text}</p>
                          </div>
                        ))}
                      </>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search */}
      <div className="rag-search-card">
        <div className="rag-search-card__head">Search Policies</div>
        <div className="rag-search-bar">
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="e.g. refund period, damaged goods, shipping SLA..."
          />
          <button type="button" onClick={handleSearch} disabled={searching}>
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="rag-results">
            <p className="rag-results__count">{searchResults.length} result{searchResults.length !== 1 ? 's' : ''}</p>
            {searchResults.map((r, i) => (
              <div key={i} className="rag-result">
                <div className="rag-result__header">
                  <span className="rag-result__cat" style={{ color: catColor(r.category), background: `${catColor(r.category)}18` }}>
                    {r.category}
                  </span>
                  <strong className="rag-result__policy">{r.policy_title}</strong>
                  {r.heading && <span className="rag-result__heading">&rsaquo; {r.heading}</span>}
                  <span className="rag-result__spacer" />
                  {r.page_number != null && <span className="rag-result__page">p.{r.page_number}</span>}
                  {r.tags.map(tag => (
                    <span key={tag} className="rag-chunk__tag" style={{ color: catColor(tag), background: `${catColor(tag)}20` }}>
                      {tag}
                    </span>
                  ))}
                </div>
                <p className="rag-result__text">{r.chunk_text}</p>
              </div>
            ))}
          </div>
        )}

        {!searchResults.length && searchQuery && !searching && (
          <p className="rag-results__empty">No results for "{searchQuery}"</p>
        )}
      </div>

    </div>
  )
}