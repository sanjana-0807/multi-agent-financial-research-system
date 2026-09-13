// frontend/src/pages/ReportPage.jsx
import { useEffect, useState } from 'react'
import { FileText, Sparkles, Cpu, GitCompare, Trash2, History, CheckCircle2 } from 'lucide-react'
import Button from '../components/Button.jsx'
import Badge from '../components/Badge.jsx'
import ReportPreview from '../features/report/ReportPreview.jsx'
import ReportExportButton from '../features/report/ReportExportButton.jsx'
import useReportGeneration from '../features/report/useReportGeneration.js'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

const STATUS_BADGE = {
  completed: 'success',
  generating: 'processing',
  failed: 'danger',
}

function ReportPage() {
  const { activeWorkspace, companies, activeCompany, selectCompany } = useWorkspace()

  const {
    report,
    setReport,
    reports,
    availableComparisons,
    loading,
    loadingComparisons,
    error,
    generate,
    loadAvailableComparisons,
    loadReports,
    removeReport,
  } = useReportGeneration()

  const [selectedComparisonIds, setSelectedComparisonIds] = useState([])

  // Whenever the active company changes, refresh what comparisons could
  // be included and what reports already exist for it, and clear any
  // report currently on screen (it belongs to the previous company).
  useEffect(() => {
    setReport(null)
    setSelectedComparisonIds([])
    if (activeCompany && activeWorkspace) {
      loadAvailableComparisons(activeCompany.id, activeWorkspace.id)
      loadReports(activeCompany.id)
    }
  }, [activeCompany?.id, activeWorkspace?.id])

  function toggleComparison(comparisonId) {
    setSelectedComparisonIds((prev) =>
      prev.includes(comparisonId)
        ? prev.filter((id) => id !== comparisonId)
        : [...prev, comparisonId]
    )
  }

  async function handleGenerate() {
    if (!activeWorkspace || !activeCompany) return
    await generate(activeWorkspace.id, activeCompany.id, selectedComparisonIds)
  }

  async function handleSwitchCompany(companyId) {
    const company = companies.find((c) => c.id === companyId)
    if (company) await selectCompany(company)
  }

  if (!activeWorkspace) {
    return (
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-3d-subtle space-y-2">
          <FileText size={32} className="text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">No Active Session</h3>
          <p className="text-sm text-slate-500">Open or create a workspace before generating a report.</p>
        </div>
      </div>
    )
  }

  if (companies.length === 0) {
    return (
      <div className="p-6 md:p-8 max-w-5xl mx-auto">
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center shadow-3d-subtle space-y-2">
          <FileText size={32} className="text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">No Companies Yet</h3>
          <p className="text-sm text-slate-500">Upload a document for this session before generating a report.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6 animate-fadeIn select-none">
      {/* Configuration strip */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle space-y-5 no-print">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
              <Sparkles size={14} /> Report Agent
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Executive Research Report</h1>
            <p className="text-sm font-medium text-slate-500 mt-1">
              Generates an Executive Summary and Outlook from this company's key financials, red flags,
              and peer comparisons, and renders a downloadable PDF.
            </p>
          </div>
          {report?.status === 'completed' && (
            <ReportExportButton reportId={report.id} filename={report.filename} />
          )}
        </div>

        {/* Company selector */}
        <div className="pt-3 border-t border-slate-100 flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Company:</span>
          <select
            value={activeCompany?.id || ''}
            onChange={(e) => handleSwitchCompany(e.target.value)}
            className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 outline-none"
          >
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.ticker})
              </option>
            ))}
          </select>
        </div>

        {/* Comparison selection */}
        <div className="pt-3 border-t border-slate-100 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <GitCompare size={13} /> Peer Comparisons to Include
          </div>
          {loadingComparisons ? (
            <p className="text-xs text-slate-400">Checking available comparisons&hellip;</p>
          ) : availableComparisons.length === 0 ? (
            <p className="text-xs text-slate-400">
              No completed comparisons involve this company yet. The report will be generated without a peer
              comparison section.
            </p>
          ) : (
            <>
              <p className="text-xs text-slate-400">
                Leave all unchecked to auto-include every completed comparison for this company.
              </p>
              <div className="flex flex-wrap gap-2">
                {availableComparisons.map((c) => {
                  const isSelected = selectedComparisonIds.includes(c.comparison_id)
                  return (
                    <button
                      key={c.comparison_id}
                      onClick={() => toggleComparison(c.comparison_id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {isSelected && <CheckCircle2 size={13} />}
                      {c.tickers.join(' vs ')}
                    </button>
                  )
                })}
              </div>
            </>
          )}
        </div>

        <Button
          onClick={handleGenerate}
          disabled={!activeCompany || loading}
          loading={loading}
          icon={Cpu}
          variant="primary"
          size="md"
          className="w-full"
        >
          Generate Report
        </Button>

        {error && (
          <p className="text-xs font-semibold text-rose-600 bg-rose-50 p-3 rounded-xl border border-rose-200">
            {error}
          </p>
        )}
      </div>

      {/* Report history for this company */}
      {reports.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-3d-subtle space-y-3 no-print">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <History size={13} /> Previous Reports
          </div>
          <div className="space-y-2">
            {reports.map((r) => (
              <div
                key={r.id}
                className={`flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border transition-colors ${
                  report?.id === r.id ? 'border-blue-400 bg-blue-50/40' : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                <button onClick={() => setReport(r)} className="flex items-center gap-3 text-left flex-1 min-w-0">
                  <Badge variant={STATUS_BADGE[r.status] || 'default'}>{r.status}</Badge>
                  <span className="text-xs font-bold text-slate-800 truncate">
                    FY {r.fiscal_year || 'N/A'} &middot; {new Date(r.created_at).toLocaleString()}
                  </span>
                </button>
                <button
                  onClick={() => removeReport(r.id, activeCompany.id)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors flex-shrink-0"
                  title="Delete report"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Printable report preview */}
      <ReportPreview report={report} />
    </div>
  )
}

export default ReportPage