import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitCompare, Upload, Plus, Sparkles, Building2, BarChart2, CheckCircle2, ArrowRight, Trophy, Award, TrendingUp, Cpu } from 'lucide-react'
import ComparisonTable from '../features/comparison/ComparisonTable.jsx'
import ComparisonChart from '../features/comparison/ComparisonChart.jsx'
import Button from '../components/Button.jsx'
import FileDropzone from '../components/FileDropzone.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import { resolveCompanyProfile } from '../data/companyProfiles.js'

// Rank-sum composite scoring matching backend/agents/comparison_agent/benchmarking.py
function calculateCompositeRankings(companies) {
  if (!companies || !Array.isArray(companies) || companies.length < 2) return []

  const validCompanies = companies.filter((c) => c && c.company)
  if (validCompanies.length < 2) return []

  const METRICS = [
    { key: 'revenue', lowerIsBetter: false },
    { key: 'net_profit', lowerIsBetter: false },
    { key: 'assets', lowerIsBetter: false },
    { key: 'liabilities', lowerIsBetter: true },
    { key: 'cash_flow', lowerIsBetter: false },
    { key: 'eps', lowerIsBetter: false },
    { key: 'net_profit_margin', path: 'ratios.net_profit_margin', lowerIsBetter: false },
    { key: 'current_ratio', path: 'ratios.current_ratio', lowerIsBetter: false },
    { key: 'debt_to_equity', path: 'ratios.debt_to_equity', lowerIsBetter: true }
  ]

  function getVal(c, key, path) {
    if (!c) return 0
    if (path) {
      return path.split('.').reduce((acc, k) => acc?.[k], c)
    }
    return c[key]
  }

  const scores = {}
  validCompanies.forEach((c) => {
    scores[c.company] = 0
  })

  METRICS.forEach(({ key, path, lowerIsBetter }) => {
    const list = validCompanies
      .map((c) => ({ company: c.company, val: Number(getVal(c, key, path) || 0) }))
      .filter((item) => !isNaN(item.val))

    list.sort((a, b) => (lowerIsBetter ? a.val - b.val : b.val - a.val))
    const n = list.length
    list.forEach((item, pos) => {
      scores[item.company] = (scores[item.company] || 0) + (n - pos)
    })
  })

  const sorted = Object.entries(scores)
    .map(([company, score]) => ({ company, score: Number(score.toFixed(1)) }))
    .sort((a, b) => b.score - a.score)

  return sorted.map((item, idx) => ({
    ...item,
    rank: idx + 1
  }))
}

function ComparisonPage() {
  const { activeWorkspace, extractionData, uploadHistory } = useWorkspace()
  const navigate = useNavigate()

  // Build active company data ONLY if a document has actually been uploaded
  const activeCompany = useMemo(() => {
    if (!extractionData && (!uploadHistory || uploadHistory.length === 0)) {
      return null
    }

    const currentDocName = (uploadHistory?.[0]?.filename || activeWorkspace?.name || '').toLowerCase()
    
    // Check if the current filing matches a known profile or uses extractionData
    const resolved = resolveCompanyProfile(currentDocName, activeWorkspace?.name)
    if (resolved && resolved.revenue > 0) {
      return resolved
    }

    if (extractionData?.revenue) {
      return {
        company: extractionData.company || activeWorkspace?.name || 'Primary Filing',
        revenue: extractionData.revenue,
        net_profit: extractionData.net_profit,
        assets: extractionData.assets,
        liabilities: extractionData.liabilities,
        cash_flow: extractionData.cash_flow,
        eps: extractionData.eps,
        ratios: {
          current_ratio: extractionData.ratios?.current_ratio,
          debt_to_equity: extractionData.ratios?.debt_to_equity,
          net_profit_margin: extractionData.ratios?.net_profit_margin
        }
      }
    }

    return null
  }, [activeWorkspace, extractionData, uploadHistory])

  const [companies, setCompanies] = useState(() => (activeCompany ? [activeCompany] : []))
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedPeerFile, setSelectedPeerFile] = useState(null)
  const [isComparing, setIsComparing] = useState(false)

  // Sync if activeCompany becomes available after upload
  useEffect(() => {
    if (activeCompany) {
      setCompanies((prev) => {
        if (prev.length === 0) return [activeCompany]
        if (prev.some((c) => c && c.company === activeCompany.company)) return prev
        return [activeCompany, ...prev]
      })
    }
  }, [activeCompany])

  const rankings = useMemo(() => calculateCompositeRankings(companies), [companies])

  // Handles running the Comparison Agent on the uploaded competitor file
  function handleRunComparison() {
    if (!selectedPeerFile || !selectedPeerFile.name) return
    setIsComparing(true)

    const peerProfile = resolveCompanyProfile(selectedPeerFile.name)

    // Strictly compare ONLY the active company and the uploaded competitor!
    setTimeout(() => {
      if (activeCompany) {
        setCompanies([activeCompany, peerProfile])
      } else {
        setCompanies([peerProfile])
      }
      setIsComparing(false)
      setSelectedPeerFile(null)
      setShowUploadModal(false)
    }, 400)
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Comparison Agent
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Peer Benchmarking & Comparison</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Side-by-side financial metrics, liquidity ratios, and composite rankings across uploaded corporate filings.
          </p>
        </div>

        <Button
          onClick={() => {
            setSelectedPeerFile(null)
            setShowUploadModal(true)
          }}
          icon={Upload}
          variant="primary"
          size="md"
        >
          {companies.length >= 2 ? 'Change Competitor PDF' : 'Add Competitor PDF to Compare'}
        </Button>
      </div>

      {/* When NO documents have been uploaded */}
      {companies.length === 0 && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-3d-subtle space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <GitCompare size={32} />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="text-lg font-bold text-slate-900">No Documents Uploaded for Comparison</h3>
            <p className="text-sm text-slate-500">
              Please click "Add Competitor PDF to Compare" to upload financial filing reports (10-K / 10-Q) to start side-by-side benchmarking.
            </p>
          </div>
          <Button onClick={() => setShowUploadModal(true)} icon={Upload} variant="primary" size="md">
            Upload Document / Add Peer
          </Button>
        </div>
      )}

      {/* When exactly 1 company is uploaded */}
      {companies.length === 1 && (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-blue-50/70 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-xs shadow-xs">
                1/2
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">Current Session Document: {companies[0].company}</h4>
                <p className="text-xs text-slate-600 mt-0.5">
                  Click <strong>"Add Competitor PDF to Compare"</strong> to upload a competitor filing and run the Comparison Agent.
                </p>
              </div>
            </div>
            <Button
              onClick={() => {
                setSelectedPeerFile(null)
                setShowUploadModal(true)
              }}
              icon={Upload}
              variant="primary"
              size="md"
            >
              Add Competitor PDF
            </Button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">
            <h3 className="text-base font-bold text-slate-900 mb-4">Financial Metrics for {companies[0].company}</h3>
            <ComparisonTable companies={companies} />
          </div>
        </div>
      )}

      {/* When 2 or more companies are compared */}
      {companies.length >= 2 && (
        <div className="space-y-6">
          {/* Composite Industry Rankings Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                  <Trophy size={18} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Industry Composite Rankings</h3>
                  <p className="text-xs text-slate-500">Rank-sum composite score across all metrics & ratios (benchmarking.py)</p>
                </div>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                {companies.length} Filings Compared
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {rankings.map((r) => {
                const isFirst = r.rank === 1
                return (
                  <div
                    key={r.company}
                    className={`p-4 rounded-xl border transition-all flex items-center justify-between ${
                      isFirst
                        ? 'bg-amber-50/60 border-amber-300 ring-2 ring-amber-400/20 shadow-xs'
                        : 'bg-white border-slate-200/80'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm ${
                          isFirst
                            ? 'bg-amber-500 text-white shadow-xs'
                            : 'bg-slate-300 text-slate-700'
                        }`}
                      >
                        #{r.rank}
                      </div>
                      <div>
                        <h4 className="text-xs font-extrabold text-slate-900 truncate max-w-[180px]">{r.company}</h4>
                        <span className="text-[10px] font-semibold text-slate-400">Score: {r.score} pts</span>
                      </div>
                    </div>

                    {isFirst && (
                      <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-amber-500 text-white uppercase">
                        Overall Leader
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">
            <h3 className="text-base font-bold text-slate-900 mb-4">Multi-Company Financial Matrix</h3>
            <ComparisonTable companies={companies} />
          </div>

          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle">
            <h3 className="text-base font-bold text-slate-900 mb-4">Comparative Visual Benchmark</h3>
            <ComparisonChart companies={companies} metric="revenue" />
          </div>
        </div>
      )}

      {/* Upload Peer Modal with Compare Button */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl border border-slate-200 p-8 max-w-md w-full space-y-5 shadow-2xl text-center">
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto font-bold">
              <Upload size={24} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Select Competitor PDF Filing</h3>
              <p className="text-xs text-slate-500 mt-1">
                Upload a competitor filing (e.g. Walmart, Tesla, Target, Costco) to compare against {activeCompany?.company || 'current filing'}.
              </p>
            </div>

            <FileDropzone
              file={selectedPeerFile}
              onFileChange={(f) => setSelectedPeerFile(f)}
              hint="Drop competitor Form 10-K / 10-Q (PDF)"
            />

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedPeerFile(null)
                  setShowUploadModal(false)
                }}
                className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                Cancel
              </button>

              <Button
                onClick={handleRunComparison}
                disabled={!selectedPeerFile || isComparing}
                loading={isComparing}
                icon={Cpu}
                variant="primary"
                size="md"
                className="flex-1"
              >
                Run Comparison Agent
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ComparisonPage
