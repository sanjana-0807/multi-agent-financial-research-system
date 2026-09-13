import { useState, useEffect } from 'react'
import {
  GitCompare,
  Upload,
  Sparkles,
  Trophy,
  Cpu,
  CheckCircle2,
  Loader2,
  History,
  Plus,
  ChevronRight,
} from 'lucide-react'
import Button from '../components/Button.jsx'
import FileDropzone from '../components/FileDropzone.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { listCompanies } from '../api/companiesApi.js'
import { uploadDocument } from '../api/documentsApi.js'
import { runExtraction } from '../api/extractionApi.js'
import { runRedFlagAnalysis } from '../api/redFlagsApi.js'
import { runComparison, listComparisons, getComparison } from '../api/comparisonApi.js'

function ComparisonPage() {
  const { activeWorkspace, addCompany } = useWorkspace()

  const [companies, setCompanies] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [loadingCompanies, setLoadingCompanies] = useState(true)

  const [showAddModal, setShowAddModal] = useState(false)
  const [peerName, setPeerName] = useState('')
  const [peerTicker, setPeerTicker] = useState('')
  const [peerFile, setPeerFile] = useState(null)
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState(null)

  const [comparing, setComparing] = useState(false)
  const [compareError, setCompareError] = useState(null)
  const [result, setResult] = useState(null)
  const [comparisonHistory, setComparisonHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [historyError, setHistoryError] = useState(null)
  const [selectedHistoryId, setSelectedHistoryId] = useState(null)
  const [loadingHistoryItem, setLoadingHistoryItem] = useState(false)

  async function refreshCompanies() {
    if (!activeWorkspace) return
    setLoadingCompanies(true)

    try {
      const res = await listCompanies(activeWorkspace.id)
      setCompanies(res.data)
    } finally {
      setLoadingCompanies(false)
    }
  }

  async function refreshComparisonHistory(companyList = companies) {
    setLoadingHistory(true)
    setHistoryError(null)

    try {
      const res = await listComparisons(0, 50)
      const history = Array.isArray(res.data) ? res.data : []

      // The current backend history endpoint is not workspace-scoped.
      // Keep only comparisons whose companies belong to the active workspace.
      if (companyList.length > 0) {
        const workspaceCompanyIds = new Set(companyList.map((company) => company.id))
        const filteredHistory = history.filter((item) =>
          Array.isArray(item.company_ids)
            ? item.company_ids.every((id) => workspaceCompanyIds.has(id))
            : true
        )
        setComparisonHistory(filteredHistory)
      } else {
        setComparisonHistory(history)
      }
    } catch (err) {
      setHistoryError(
        err.response?.data?.detail || 'Failed to load comparison history'
      )
      setComparisonHistory([])
    } finally {
      setLoadingHistory(false)
    }
  }

  useEffect(() => {
    async function loadWorkspaceData() {
      if (!activeWorkspace) return

      setResult(null)
      setSelectedIds([])
      setSelectedHistoryId(null)

      setLoadingCompanies(true)
      try {
        const companiesRes = await listCompanies(activeWorkspace.id)
        const workspaceCompanies = companiesRes.data || []
        setCompanies(workspaceCompanies)
        await refreshComparisonHistory(workspaceCompanies)
      } finally {
        setLoadingCompanies(false)
      }
    }

    loadWorkspaceData()
  }, [activeWorkspace])

  function toggleSelect(id) {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < 2
          ? [...prev, id]
          : [prev[1], id]
    )
  }

  async function handleAddPeer() {
    if (!peerName.trim() || !peerTicker.trim() || !peerFile) return

    setAdding(true)
    setAddError(null)

    try {
      const company = await addCompany({
        name: peerName.trim(),
        ticker: peerTicker.trim().toUpperCase(),
      })

      const uploadRes = await uploadDocument(peerFile, company.id)
      const documentId = uploadRes.data.document_id

      await runExtraction(documentId)
      await runRedFlagAnalysis(documentId)

      await refreshCompanies()

      setPeerName('')
      setPeerTicker('')
      setPeerFile(null)
      setShowAddModal(false)
    } catch (err) {
      setAddError(
        err.response?.data?.detail ||
          'Failed to add and process competitor document'
      )
    } finally {
      setAdding(false)
    }
  }

  async function handleRunComparison() {
    if (!activeWorkspace || selectedIds.length !== 2) return

    setComparing(true)
    setCompareError(null)

    try {
      const res = await runComparison(activeWorkspace.id, selectedIds)
      setResult(res.data)
      setSelectedHistoryId(res.data?.id || null)
      await refreshComparisonHistory(companies)
    } catch (err) {
      setCompareError(
        err.response?.data?.detail ||
          'Comparison failed — make sure both companies have a processed document.'
      )
    } finally {
      setComparing(false)
    }
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn select-none">

      {/* =========================================================
          HEADER
      ========================================================== */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} />
            Comparison Agent
          </div>

          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Peer Benchmarking & Comparison
          </h1>

          <p className="text-sm font-medium text-slate-500 mt-1">
            Select exactly two companies to compare.
          </p>
        </div>

        <Button
          onClick={() => setShowAddModal(true)}
          icon={Upload}
          variant="primary"
          size="md"
        >
          Add Competitor Company
        </Button>
      </div>

      {/* =========================================================
          MAIN CONTENT
      ========================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)] gap-6 items-start">

        {/* =======================================================
            COMPARISON HISTORY SIDEBAR
            UI ONLY — NO LOGIC/API CHANGES
        ======================================================== */}
        <aside className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle overflow-hidden lg:sticky lg:top-6">

          {/* History Header */}
          <div className="p-4 border-b border-slate-100 bg-white">
            <div className="flex items-center justify-between gap-3">

              <div className="flex items-center gap-2 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <History size={16} />
                </div>

                <div className="min-w-0">
                  <h3 className="text-sm font-extrabold text-slate-900">
                    Comparison History
                  </h3>

                  <p className="text-[10px] font-medium text-slate-400 mt-0.5">
                    Previous comparisons
                  </p>
                </div>
              </div>

              {/* UI button only — deliberately does not alter logic */}
              <button
                type="button"
                className="w-8 h-8 rounded-lg border border-slate-200 text-slate-500 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50 transition-colors flex items-center justify-center shrink-0"
                title="New comparison"
                onClick={() => {
                  setResult(null)
                  setSelectedIds([])
                  setSelectedHistoryId(null)
                  setCompareError(null)
                }}
              >
                <Plus size={16} />
              </button>

            </div>
          </div>

          {/* History List */}
          <div className="p-3 max-h-[520px] overflow-y-auto">
            {loadingHistory ? (
              <div className="py-10 px-4 text-center">
                <Loader2 size={20} className="animate-spin text-blue-500 mx-auto mb-3" />
                <p className="text-xs font-bold text-slate-600">
                  Loading comparison history...
                </p>
              </div>
            ) : historyError ? (
              <div className="py-8 px-4 text-center">
                <div className="w-11 h-11 rounded-xl bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-3">
                  <History size={20} />
                </div>
                <p className="text-xs font-bold text-rose-600">
                  Unable to load history
                </p>
                <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                  {historyError}
                </p>
                <button
                  type="button"
                  onClick={() => refreshComparisonHistory(companies)}
                  className="mt-3 text-[10px] font-bold text-blue-600 hover:text-blue-700"
                >
                  Try again
                </button>
              </div>
            ) : comparisonHistory.length > 0 ? (
              <div className="space-y-2">
                <div className="text-[9px] font-bold uppercase tracking-wider text-slate-400 px-2 pb-1">
                  Previous comparisons
                </div>

                {comparisonHistory.map((item) => {
                  const isActive = selectedHistoryId === item.id
                  const comparisonDate = item.completed_at || item.created_at

                  return (
                    <button
                      key={item.id}
                      type="button"
                      disabled={loadingHistoryItem}
                      onClick={async () => {
                        if (!item.id) return

                        setSelectedHistoryId(item.id)
                        setLoadingHistoryItem(true)
                        setCompareError(null)

                        try {
                          const res = await getComparison(item.id)
                          setResult(res.data)
                          setSelectedIds(res.data?.company_ids || [])
                        } catch (err) {
                          setCompareError(
                            err.response?.data?.detail ||
                              'Failed to load the saved comparison.'
                          )
                        } finally {
                          setLoadingHistoryItem(false)
                        }
                      }}
                      className={`w-full text-left rounded-xl border p-3 transition-colors ${
                        isActive
                          ? 'border-blue-200 bg-blue-50/70'
                          : 'border-slate-200 bg-white hover:border-blue-200 hover:bg-blue-50/40'
                      } ${loadingHistoryItem ? 'opacity-70' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <GitCompare
                              size={13}
                              className={isActive ? 'text-blue-600 shrink-0' : 'text-slate-400 shrink-0'}
                            />
                            <span className="text-xs font-extrabold text-slate-900 truncate">
                              {item.tickers?.join(' vs ') || 'Comparison'}
                            </span>
                          </div>

                          <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">
                            {item.summary || 'Completed comparison'}
                          </p>
                        </div>

                        <ChevronRight
                          size={14}
                          className={isActive ? 'text-blue-500 shrink-0 mt-0.5' : 'text-slate-300 shrink-0 mt-0.5'}
                        />
                      </div>

                      <div className="flex items-center justify-between gap-2 mt-2">
                        <div className="flex items-center gap-1.5">
                          <span className={`w-1.5 h-1.5 rounded-full ${item.status === 'completed' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                          <span className={`text-[9px] font-bold ${item.status === 'completed' ? 'text-emerald-600' : 'text-amber-600'}`}>
                            {item.status || 'Saved'}
                          </span>
                        </div>

                        {comparisonDate && (
                          <span className="text-[9px] text-slate-400">
                            {new Date(comparisonDate).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            ) : (
              <div className="py-10 px-4 text-center">
                <div className="w-11 h-11 rounded-xl bg-slate-50 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <History size={20} />
                </div>

                <p className="text-xs font-bold text-slate-600">
                  No comparison history
                </p>

                <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                  Your completed comparisons will appear here.
                </p>
              </div>
            )}
          </div>

          {/* New Comparison Footer */}
          <div className="p-3 border-t border-slate-100 bg-slate-50/60">

            <button
              type="button"
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border border-slate-200 bg-white text-xs font-bold text-slate-700 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-colors"
              onClick={() => {
                setResult(null)
                setSelectedIds([])
                setSelectedHistoryId(null)
                setCompareError(null)
              }}
            >
              <Plus size={14} />
              New Comparison
            </button>

          </div>

        </aside>

        {/* =======================================================
            CURRENT COMPARISON AREA
        ======================================================== */}
        <main className="min-w-0 space-y-6">

          {/* =====================================================
              COMPANY SELECTION
          ====================================================== */}
          {loadingCompanies ? (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle text-center py-12 text-xs text-slate-400">
              Loading companies...
            </div>
          ) : companies.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-3d-subtle space-y-4">

              <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <GitCompare size={32} />
              </div>

              <h3 className="text-lg font-bold text-slate-900">
                No Companies Yet
              </h3>

              <p className="text-sm text-slate-500">
                Upload a document for this session first.
              </p>

            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">

              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Select Two Companies
                  </h3>

                  <p className="text-[10px] text-slate-400 mt-1">
                    Choose two companies to benchmark against each other.
                  </p>
                </div>

                <div className="shrink-0 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-[10px] font-bold text-slate-500">
                  {selectedIds.length}/2 Selected
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">

                {companies.map((c) => {
                  const isSelected = selectedIds.includes(c.id)

                  return (
                    <button
                      key={c.id}
                      onClick={() => toggleSelect(c.id)}
                      className={`flex items-center justify-between px-3.5 py-3 rounded-xl border text-left transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-900 truncate">
                          {c.name}
                        </div>

                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {c.ticker}
                        </div>
                      </div>

                      {isSelected && (
                        <CheckCircle2
                          size={16}
                          className="text-blue-600 shrink-0"
                        />
                      )}
                    </button>
                  )
                })}

              </div>

              <Button
                onClick={handleRunComparison}
                disabled={selectedIds.length !== 2 || comparing}
                loading={comparing}
                icon={Cpu}
                variant="primary"
                size="md"
                className="w-full"
              >
                Compare Selected Companies
              </Button>

              {compareError && (
                <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-3 rounded-xl border border-rose-200">
                  {compareError}
                </p>
              )}

            </div>
          )}

          {/* =====================================================
              RESULT
          ====================================================== */}
          {result && (
            <div className="space-y-6">

              {/* Industry Rankings */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">

                <div className="flex items-center gap-2.5">

                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                    <Trophy size={18} />
                  </div>

                  <div className="min-w-0">
                    <h3 className="text-base font-bold text-slate-900">
                      Industry Rankings
                    </h3>

                    <p className="text-xs text-slate-500 mt-0.5">
                      {result.summary}
                    </p>
                  </div>

                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">

                  {result.industry_rankings.map((r) => (
                    <div
                      key={r.ticker}
                      className={`p-4 rounded-xl border flex items-center justify-between ${
                        r.rank === 1
                          ? 'bg-amber-50/60 border-amber-300'
                          : 'bg-white border-slate-200/80'
                      }`}
                    >
                      <div className="flex items-center gap-3">

                        <div
                          className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm ${
                            r.rank === 1
                              ? 'bg-amber-500 text-white'
                              : 'bg-slate-300 text-slate-700'
                          }`}
                        >
                          #{r.rank}
                        </div>

                        <div>
                          <h4 className="text-xs font-extrabold text-slate-900">
                            {r.ticker}
                          </h4>

                          <span className="text-[10px] font-semibold text-slate-400">
                            Score: {r.score}
                          </span>
                        </div>

                      </div>
                    </div>
                  ))}

                </div>

              </div>

              {/* Ratio Comparison */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">

                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Ratio Comparison
                    </h3>

                    <p className="text-[10px] text-slate-400 mt-1">
                      Financial benchmark across selected companies
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">

                    <thead className="text-slate-500 border-b border-slate-200">
                      <tr>
                        <th className="py-2 pr-4">
                          Metric
                        </th>

                        {Object.keys(
                          result.ratio_comparisons[0]?.values || {}
                        ).map((ticker) => (
                          <th
                            key={ticker}
                            className="py-2 pr-4"
                          >
                            {ticker}
                          </th>
                        ))}

                        <th className="py-2">
                          Best
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-100">

                      {result.ratio_comparisons.map((row) => (
                        <tr key={row.ratio_name}>

                          <td className="py-2 pr-4 font-semibold text-slate-800">
                            {row.ratio_name}
                          </td>

                          {Object.entries(row.values).map(
                            ([ticker, val]) => (
                              <td
                                key={ticker}
                                className="py-2 pr-4"
                              >
                                {val}
                              </td>
                            )
                          )}

                          <td className="py-2 font-bold text-emerald-600">
                            {row.best_performer}
                          </td>

                        </tr>
                      ))}

                    </tbody>

                  </table>
                </div>

              </div>

              {/* Run Again */}
              <div className="flex justify-end">

                <Button
                  onClick={() => {
                    setResult(null)
                    setSelectedIds([])
                    setSelectedHistoryId(null)
                    setCompareError(null)
                  }}
                  variant="outline"
                  size="sm"
                >
                  Run Again
                </Button>

              </div>

            </div>
          )}

        </main>

      </div>

      {/* =========================================================
          ADD COMPETITOR MODAL
      ========================================================== */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">

          <div className="bg-white rounded-3xl border border-slate-200 p-8 max-w-md w-full space-y-4 shadow-2xl">

            <div className="text-center space-y-1">

              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <Upload size={24} />
              </div>

              <h3 className="text-lg font-bold text-slate-900">
                Add Competitor Company
              </h3>

            </div>

            <input
              type="text"
              placeholder="Company name"
              value={peerName}
              onChange={(e) => setPeerName(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs"
            />

            <input
              type="text"
              placeholder="Ticker"
              value={peerTicker}
              onChange={(e) => setPeerTicker(e.target.value)}
              maxLength={10}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs"
            />

            <FileDropzone
              file={peerFile}
              onFileSelect={setPeerFile}
              hint="Drop competitor Form 10-K / 10-Q (PDF)"
            />

            {addError && (
              <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                {addError}
              </p>
            )}

            <div className="flex gap-2 pt-2">

              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>

              <Button
                onClick={handleAddPeer}
                disabled={
                  !peerName.trim() ||
                  !peerTicker.trim() ||
                  !peerFile ||
                  adding
                }
                loading={adding}
                icon={adding ? Loader2 : CheckCircle2}
                variant="primary"
                size="md"
                className="flex-1"
              >
                Add & Process
              </Button>

            </div>

          </div>

        </div>
      )}

    </div>
  )
}

export default ComparisonPage