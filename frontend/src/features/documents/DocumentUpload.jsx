import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UploadCloud, CheckCircle2, AlertCircle, Cpu, Sparkles,
  Database, ShieldCheck, Loader2, AlertTriangle, Building2, Check,
  Pencil, Trash2
} from 'lucide-react'
import FileDropzone from '../../components/FileDropzone.jsx'
import Button from '../../components/Button.jsx'
import { uploadDocument } from '../../api/documentsApi.js'
import { runExtraction } from '../../api/extractionApi.js'
import { runRedFlagAnalysis } from '../../api/redFlagsApi.js'
import { getLatestDocumentForCompany } from '../../api/documentsApi.js'
import { updateCompany, deleteCompany } from '../../api/companiesApi.js'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

const PIPELINE_STEPS = [
  {
    num: 1,
    agent: 'Document Agent',
    label: 'Document Ingestion & ChromaDB Indexing',
    desc: 'Extracting raw disclosure text, chunking, and generating vector embeddings in ChromaDB.',
    icon: Database,
    color: 'text-blue-700 bg-blue-100 border-blue-200'
  },
  {
    num: 2,
    agent: 'Extraction Agent',
    label: 'KPI & Financial Metrics Extraction',
    desc: 'Running LLM reasoning to extract revenue, net profit, margins, EPS, and leverage ratios.',
    icon: Cpu,
    color: 'text-indigo-700 bg-indigo-100 border-indigo-200'
  },
  {
    num: 3,
    agent: 'Red Flag Agent',
    label: 'Risk Anomaly & Auditor Qualification Scan',
    desc: 'Evaluating leverage, margins, liquidity, and auditor remarks for risk signals.',
    icon: ShieldCheck,
    color: 'text-amber-700 bg-amber-100 border-amber-200'
  }
]

function isFinancialDocument(fileName) {
  if (!fileName) return false
  const lower = fileName.toLowerCase()
  return ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.txt'].some((ext) => lower.endsWith(ext))
}

function DocumentUpload() {
  const navigate = useNavigate()
  const {
    activeWorkspace,
    companies,
    activeCompany,
    addCompany,
    selectCompany,
    refreshCompanies,
    setPipelineResults,
  } = useWorkspace()

  // Keep the upload page in sync with the active workspace.
  // The workspace can open before its company list has finished loading,
  // so refresh it here instead of rendering an empty company selector.
  useEffect(() => {
    if (!activeWorkspace?.id || companies.length > 0) return

    let cancelled = false

    async function loadCompanies() {
      try {
        const loadedCompanies = await refreshCompanies()

        if (cancelled || !Array.isArray(loadedCompanies)) return
      } catch (error) {
        if (!cancelled) {
          console.error(
            'Failed to load companies for active workspace:',
            error
          )
        }
      }
    }

    loadCompanies()

    return () => {
      cancelled = true
    }
  }, [activeWorkspace?.id, companies.length])

  // Which companies already have a document.
  // Requests run in parallel so one slow company does not delay the others.
  const [docStatusByCompany, setDocStatusByCompany] = useState({})

  useEffect(() => {
    let cancelled = false

    async function checkAll() {
      const entries = await Promise.all(
        companies.map(async (company) => {
          try {
            const res = await getLatestDocumentForCompany(company.id)

            return [company.id, res.data?.status || null]
          } catch {
            return [company.id, null]
          }
        })
      )

      if (!cancelled) {
        setDocStatusByCompany(Object.fromEntries(entries))
      }
    }

    if (companies.length > 0) {
      checkAll()
    } else {
      setDocStatusByCompany({})
    }

    return () => {
      cancelled = true
    }
  }, [companies])

  const [showAddCompanyForm, setShowAddCompanyForm] = useState(false)
  const [companyName, setCompanyName] = useState('')
  const [ticker, setTicker] = useState('')
  const [addingCompany, setAddingCompany] = useState(false)
  const [companyError, setCompanyError] = useState(null)

  // --- Rename / Delete company state ---
  const [editingCompanyId, setEditingCompanyId] = useState(null)
  const [editName, setEditName] = useState('')
  const [editTicker, setEditTicker] = useState('')
  const [renaming, setRenaming] = useState(false)
  const [deletingCompanyId, setDeletingCompanyId] = useState(null)

  const [file, setFile] = useState(null)
  const [pipelineActive, setPipelineActive] = useState(false)
  const [activeStepIndex, setActiveStepIndex] = useState(0)
  const [completedSteps, setCompletedSteps] = useState([])
  const [validationError, setValidationError] = useState(null)
  const [pipelineError, setPipelineError] = useState(null)

  async function handleCreateCompany(e) {
    e.preventDefault()
    if (!companyName.trim() || !ticker.trim()) return

    setAddingCompany(true)
    setCompanyError(null)

    try {
      const company = await addCompany({
        name: companyName.trim(),
        ticker: ticker.trim().toUpperCase(),
      })

      // New companies have no document yet, so keep the user on
      // the upload page and select the newly created company.
      await selectCompany(company)

      setCompanyName('')
      setTicker('')
      setShowAddCompanyForm(false)
    } catch (err) {
      setCompanyError(
        err.response?.data?.detail || 'Failed to create company'
      )
    } finally {
      setAddingCompany(false)
    }
  }

  function startRename(company) {
    setEditingCompanyId(company.id)
    setEditName(company.name)
    setEditTicker(company.ticker)
    setCompanyError(null)
  }

  function cancelRename() {
    setEditingCompanyId(null)
    setEditName('')
    setEditTicker('')
  }

  async function handleRenameSubmit(e, companyId) {
    e.preventDefault()
    if (!editName.trim() || !editTicker.trim()) return

    setRenaming(true)
    setCompanyError(null)

    try {
      await updateCompany(companyId, {
        name: editName.trim(),
        ticker: editTicker.trim().toUpperCase(),
      })
      await refreshCompanies()
      cancelRename()
    } catch (err) {
      setCompanyError(err.response?.data?.detail || 'Failed to rename company')
    } finally {
      setRenaming(false)
    }
  }

  async function handleDeleteCompany(company) {
    const confirmed = window.confirm(
      `Delete "${company.name}" (${company.ticker})? This cannot be undone.`
    )
    if (!confirmed) return

    setDeletingCompanyId(company.id)
    setCompanyError(null)

    try {
      await deleteCompany(company.id)
      await refreshCompanies()
    } catch (err) {
      setCompanyError(err.response?.data?.detail || 'Failed to delete company')
    } finally {
      setDeletingCompanyId(null)
    }
  }

  async function handleCompanySelect(company) {
    if (!company) return

    setPipelineError(null)

    /*
     * If a document already exists, open the result dashboard immediately.
     * selectCompany() continues loading extraction/red-flag data in the
     * background through WorkspaceContext.
     *
     * If there is no document, stay on Upload and simply select the company
     * so the user can upload its filing.
     */
    const existingDocumentStatus = docStatusByCompany[company.id]

    if (existingDocumentStatus) {
      selectCompany(company).catch((error) => {
        console.error(
          `Failed to load company ${company.id}:`,
          error
        )
      })

      const workspaceId =
        activeWorkspace?.id || activeWorkspace?._id

      navigate(
        workspaceId
          ? `/dashboard?workspace=${workspaceId}&company=${company.id}`
          : '/dashboard'
      )

      return
    }

    await selectCompany(company)
  }

  function handleFileChange(selectedFile) {
    setFile(selectedFile)
    setValidationError(null)
    setPipelineError(null)
    setPipelineActive(false)
    setCompletedSteps([])
    setActiveStepIndex(0)

    if (selectedFile && !isFinancialDocument(selectedFile.name)) {
      setValidationError(
        `"${selectedFile.name}" is not a supported document format. Please upload a PDF, DOCX, XLSX, or CSV filing.`
      )
    }
  }

  async function handleStartPipeline() {
    if (!file) {
      setValidationError('Please select a financial filing before processing.')
      return
    }
    if (!isFinancialDocument(file.name)) {
      setValidationError(`"${file.name}" is not a supported document format.`)
      return
    }
    if (!activeCompany) {
      setPipelineError('Select or create a company for this document first.')
      return
    }

    setValidationError(null)
    setPipelineError(null)
    setPipelineActive(true)
    setCompletedSteps([])
    setActiveStepIndex(0)

    try {
      const uploadRes = await uploadDocument(file, activeCompany.id)
      const documentId = uploadRes.data.document_id
      setCompletedSteps((prev) => [...prev, 0])
      setActiveStepIndex(1)

      const extractionRes = await runExtraction(documentId)
      setCompletedSteps((prev) => [...prev, 1])
      setActiveStepIndex(2)

      const redFlagRes = await runRedFlagAnalysis(documentId)
      setCompletedSteps((prev) => [...prev, 2])

      setPipelineResults({
        document: { document_id: documentId, filename: file.name, status: 'indexed' },
        extraction: extractionRes.data,
        redFlags: redFlagRes.data,
      })

      setTimeout(() => {
        const workspaceId =
          activeWorkspace?.id || activeWorkspace?._id

        navigate(
          workspaceId
            ? `/dashboard?workspace=${workspaceId}&company=${activeCompany.id}`
            : '/dashboard'
        )
      }, 600)
    } catch (err) {
      setPipelineError(err.response?.data?.detail || 'Pipeline failed — please try again.')
      setPipelineActive(false)
    }
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8 animate-fadeIn select-none">
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Document Ingestion Engine
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Upload Financial Documents</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            {activeWorkspace ? `Session: ${activeWorkspace.name}` : 'Open or create a research session first.'}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/80 self-start md:self-auto">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          <span>3-Agent Pipeline Ready</span>
        </div>
      </div>

      {/* Company selector — always visible when the workspace has any companies */}
      {activeWorkspace && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Building2 size={18} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Companies in This Session</h3>
                <p className="text-xs text-slate-500 mt-0.5">Select a company to upload its filing, or add a new one.</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowAddCompanyForm((v) => !v)}
              className="text-xs font-bold text-blue-600 hover:underline"
            >
              {showAddCompanyForm ? 'Cancel' : '+ Add Company'}
            </button>
          </div>

          {companies.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {companies.map((c) => {
                const status = docStatusByCompany[c.id]
                const isSelected = activeCompany?.id === c.id
                const isEditing = editingCompanyId === c.id
                const isDeleting = deletingCompanyId === c.id

                if (isEditing) {
                  return (
                    <form
                      key={c.id}
                      onSubmit={(e) => handleRenameSubmit(e, c.id)}
                      className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl border border-blue-400 bg-blue-50/60"
                    >
                      <div className="flex-1 min-w-0 space-y-1">
                        <input
                          autoFocus
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          placeholder="Company name"
                          className="w-full bg-white border border-blue-300 rounded-lg px-2 py-1 text-xs font-bold text-slate-900"
                        />
                        <input
                          type="text"
                          value={editTicker}
                          onChange={(e) => setEditTicker(e.target.value.toUpperCase())}
                          placeholder="Ticker"
                          maxLength={10}
                          className="w-full bg-white border border-blue-300 rounded-lg px-2 py-1 text-[10px] text-slate-500"
                        />
                      </div>
                      <div className="flex flex-col items-end gap-1 flex-shrink-0">
                        <button
                          type="submit"
                          disabled={renaming || !editName.trim() || !editTicker.trim()}
                          className="text-[10px] font-bold text-blue-600 hover:underline disabled:opacity-50 whitespace-nowrap"
                        >
                          {renaming ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          type="button"
                          onClick={cancelRename}
                          className="text-[10px] font-semibold text-slate-400 hover:underline whitespace-nowrap"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )
                }

                return (
                  <div
                    key={c.id}
                    className={`group flex items-center justify-between px-3.5 py-2.5 rounded-xl border transition-colors ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => handleCompanySelect(c)}
                      className="flex-1 min-w-0 text-left"
                    >
                      <div className="text-xs font-bold text-slate-900 truncate">{c.name}</div>
                      <div className="text-[10px] text-slate-400">{c.ticker}</div>
                    </button>

                    <div className="flex items-center gap-1.5 pl-2 flex-shrink-0">
                      {status ? (
                        <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 whitespace-nowrap">
                          <Check size={12} /> {status}
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold text-slate-400 whitespace-nowrap">No document</span>
                      )}

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          startRename(c)
                        }}
                        title="Rename company"
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-slate-200 text-slate-400 hover:text-blue-600"
                      >
                        <Pencil size={12} />
                      </button>

                      <button
                        type="button"
                        disabled={isDeleting}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteCompany(c)
                        }}
                        title="Delete company"
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-rose-100 text-slate-400 hover:text-rose-600 disabled:opacity-100 disabled:cursor-not-allowed"
                      >
                        {isDeleting ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <Trash2 size={12} />
                        )}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="py-6 text-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
              <p className="text-xs font-semibold text-slate-500">
                Loading companies in this session...
              </p>
            </div>
          )}

          {showAddCompanyForm && (
            <form onSubmit={handleCreateCompany} className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100">
              <input
                type="text"
                placeholder="Company name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:col-span-1"
              />
              <input
                type="text"
                placeholder="Ticker"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                required
                maxLength={10}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs sm:col-span-1"
              />
              <Button
                type="submit"
                disabled={!companyName.trim() || !ticker.trim() || addingCompany}
                loading={addingCompany}
                variant="primary"
                size="md"
                className="sm:col-span-1"
              >
                Create
              </Button>
            </form>
          )}

          {companyError && (
            <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
              {companyError}
            </p>
          )}
        </div>
      )}

      {validationError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
          <AlertTriangle size={18} className="text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Document Ingestion Rejected</span>
            <p className="mt-0.5 text-rose-700 leading-relaxed">{validationError}</p>
          </div>
        </div>
      )}

      {pipelineError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
          <AlertCircle size={18} className="text-rose-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Pipeline Error</span>
            <p className="mt-0.5 text-rose-700 leading-relaxed">{pipelineError}</p>
          </div>
        </div>
      )}

      {activeCompany && !pipelineActive && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-8 shadow-3d-subtle space-y-6 text-center">
          <p className="text-xs font-semibold text-slate-500">
            Uploading for: <span className="text-slate-900 font-bold">{activeCompany.name} ({activeCompany.ticker})</span>
          </p>
          <FileDropzone file={file} onFileSelect={handleFileChange} />
          <div className="pt-2 flex justify-center">
            <Button
              onClick={handleStartPipeline}
              disabled={!file}
              icon={Sparkles}
              variant="primary"
              size="lg"
              className="w-full sm:w-auto shadow-lg shadow-blue-500/20"
            >
              Ingest & Process Document →
            </Button>
          </div>
        </div>
      )}

      {pipelineActive && (
        <div className="bg-white rounded-3xl p-8 border border-slate-200/80 shadow-3d-subtle space-y-6 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-blue-600">
                Live Backend Orchestration
              </span>
              <h3 className="text-xl font-extrabold text-slate-900 mt-0.5">3-Agent Sequential Pipeline</h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-bold px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700">
              <Loader2 size={13} className="animate-spin text-blue-600" />
              <span>Processing Document...</span>
            </div>
          </div>

          <div className="space-y-4">
            {PIPELINE_STEPS.map((step, idx) => {
              const isDone = completedSteps.includes(idx)
              const isActive = activeStepIndex === idx && !isDone
              return (
                <div
                  key={step.num}
                  className={`p-5 rounded-2xl border transition-all duration-500 flex items-start gap-4 ${
                    isActive
                      ? 'bg-blue-50/70 border-blue-300 shadow-md shadow-blue-500/10 scale-[1.01]'
                      : isDone
                      ? 'bg-slate-50 border-emerald-300'
                      : 'bg-slate-50/50 border-slate-200/60 opacity-60'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black flex-shrink-0 ${
                      isDone
                        ? 'bg-emerald-500 text-white'
                        : isActive
                        ? 'bg-blue-600 text-white animate-pulse'
                        : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    {isDone ? <CheckCircle2 size={20} /> : step.num}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${step.color}`}>
                          {step.agent}
                        </span>
                        <h4 className="text-sm font-bold text-slate-900">{step.label}</h4>
                      </div>
                      <span className={`text-xs font-bold ${isDone ? 'text-emerald-600' : isActive ? 'text-blue-600 animate-pulse' : 'text-slate-400'}`}>
                        {isDone ? 'Complete ✓' : isActive ? 'Working...' : 'Waiting'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default DocumentUpload