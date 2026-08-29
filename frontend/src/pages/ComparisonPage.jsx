import { useState, useEffect } from 'react'
import { GitCompare, Upload, Sparkles, Trophy, Cpu, CheckCircle2, Loader2 } from 'lucide-react'
import Button from '../components/Button.jsx'
import FileDropzone from '../components/FileDropzone.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { listCompanies } from '../api/companiesApi.js'
import { uploadDocument } from '../api/documentsApi.js'
import { runExtraction } from '../api/extractionApi.js'
import { runRedFlagAnalysis } from '../api/redFlagsApi.js'
import { runComparison } from '../api/comparisonApi.js'

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

  useEffect(() => {
    refreshCompanies()
  }, [activeWorkspace])

  function toggleSelect(id) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id]
    )
  }

  async function handleAddPeer() {
    if (!peerName.trim() || !peerTicker.trim() || !peerFile) return
    setAdding(true)
    setAddError(null)
    try {
      const company = await addCompany({ name: peerName.trim(), ticker: peerTicker.trim().toUpperCase() })
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
      setAddError(err.response?.data?.detail || 'Failed to add and process competitor document')
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
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Comparison Agent
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Peer Benchmarking & Comparison</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">Select exactly two companies to compare.</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} icon={Upload} variant="primary" size="md">
          Add Competitor Company
        </Button>
      </div>

      {loadingCompanies ? (
        <div className="text-center py-12 text-xs text-slate-400">Loading companies...</div>
      ) : companies.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-3d-subtle space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <GitCompare size={32} />
          </div>
          <h3 className="text-lg font-bold text-slate-900">No Companies Yet</h3>
          <p className="text-sm text-slate-500">Upload a document for this session first.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
          <h3 className="text-base font-bold text-slate-900">Select Two Companies</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {companies.map((c) => {
              const isSelected = selectedIds.includes(c.id)
              return (
                <button
                  key={c.id}
                  onClick={() => toggleSelect(c.id)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl border text-left transition-colors ${
                    isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div>
                    <div className="text-xs font-bold text-slate-900">{c.name}</div>
                    <div className="text-[10px] text-slate-400">{c.ticker}</div>
                  </div>
                  {isSelected && <CheckCircle2 size={16} className="text-blue-600" />}
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
            <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-3 rounded-xl border border-rose-200">{compareError}</p>
          )}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                <Trophy size={18} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Industry Rankings</h3>
                <p className="text-xs text-slate-500">{result.summary}</p>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {result.industry_rankings.map((r) => (
                <div key={r.ticker} className={`p-4 rounded-xl border flex items-center justify-between ${
                  r.rank === 1 ? 'bg-amber-50/60 border-amber-300' : 'bg-white border-slate-200/80'
                }`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm ${
                      r.rank === 1 ? 'bg-amber-500 text-white' : 'bg-slate-300 text-slate-700'
                    }`}>
                      #{r.rank}
                    </div>
                    <div>
                      <h4 className="text-xs font-extrabold text-slate-900">{r.ticker}</h4>
                      <span className="text-[10px] font-semibold text-slate-400">Score: {r.score}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">
            <h3 className="text-base font-bold text-slate-900 mb-4">Ratio Comparison</h3>
            <table className="w-full text-xs text-left">
              <thead className="text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-2 pr-4">Metric</th>
                  {Object.keys(result.ratio_comparisons[0]?.values || {}).map((ticker) => (
                    <th key={ticker} className="py-2 pr-4">{ticker}</th>
                  ))}
                  <th className="py-2">Best</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.ratio_comparisons.map((row) => (
                  <tr key={row.ratio_name}>
                    <td className="py-2 pr-4 font-semibold text-slate-800">{row.ratio_name}</td>
                    {Object.entries(row.values).map(([ticker, val]) => (
                      <td key={ticker} className="py-2 pr-4">{val}</td>
                    ))}
                    <td className="py-2 font-bold text-emerald-600">{row.best_performer}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end">
            <Button onClick={() => { setResult(null); setSelectedIds([]) }} variant="outline" size="sm">
              Run Again
            </Button>
          </div>
        </div>
      )}

      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl border border-slate-200 p-8 max-w-md w-full space-y-4 shadow-2xl">
            <div className="text-center space-y-1">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <Upload size={24} />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Add Competitor Company</h3>
            </div>
            <input type="text" placeholder="Company name" value={peerName} onChange={(e) => setPeerName(e.target.value)} className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs" />
            <input type="text" placeholder="Ticker" value={peerTicker} onChange={(e) => setPeerTicker(e.target.value)} maxLength={10} className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs" />
            <FileDropzone file={peerFile} onFileSelect={setPeerFile} hint="Drop competitor Form 10-K / 10-Q (PDF)" />
            {addError && <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">{addError}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={() => setShowAddModal(false)} className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50">Cancel</button>
              <Button onClick={handleAddPeer} disabled={!peerName.trim() || !peerTicker.trim() || !peerFile || adding} loading={adding} icon={adding ? Loader2 : CheckCircle2} variant="primary" size="md" className="flex-1">Add & Process</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ComparisonPage