// frontend/src/features/report/ReportPreview.jsx
import { FileText, Sparkles, Calendar, Award, ShieldAlert, BarChart3, GitCompare, AlertTriangle } from 'lucide-react'
import Badge from '../../components/Badge.jsx'

const STATUS_BADGE = {
  completed: 'success',
  generating: 'processing',
  failed: 'danger',
}

function SectionStatusPill({ ok, label, Icon }) {
  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold ${
        ok
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200/80'
          : 'bg-slate-50 text-slate-400 border-slate-200'
      }`}
    >
      <Icon size={14} />
      {label}
      <span className="ml-auto">{ok ? 'Included' : 'Not available'}</span>
    </div>
  )
}

function ReportPreview({ report }) {
  if (!report) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-3d-subtle">
        <FileText size={32} className="text-slate-300 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-400">
          No report generated yet for this company. Configure the sections above and generate one.
        </p>
      </div>
    )
  }

  const isFailed = report.status === 'failed'
  const isGenerating = report.status === 'generating'
  const sectionStatus = report.section_status || {}
  const comparisons = report.comparisons_included || []

  return (
    <div id="printable-report" className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle p-8 space-y-6 select-none animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Award size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600">
              <Sparkles size={12} /> Executive Financial Research Report
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-0.5">
              {report.company_name} ({report.ticker})
            </h2>
            <p className="text-xs font-semibold text-slate-400 mt-1 flex items-center gap-1.5">
              <Calendar size={13} />
              Fiscal Year {report.fiscal_year || 'N/A'}
              {report.completed_at && ` \u00b7 Completed ${new Date(report.completed_at).toLocaleDateString()}`}
            </p>
          </div>
        </div>

        <Badge variant={STATUS_BADGE[report.status] || 'default'}>
          {report.status?.toUpperCase() || 'UNKNOWN'}
        </Badge>
      </div>

      {isFailed && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs font-semibold text-rose-700 flex items-start gap-2">
          <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
          {report.error_message || 'Report generation failed.'}
        </div>
      )}

      {isGenerating && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs font-semibold text-amber-700">
          Report is still generating&hellip;
        </div>
      )}

      {/* Section availability */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <SectionStatusPill ok={!!sectionStatus.key_financials} label="Key Financials" Icon={BarChart3} />
        <SectionStatusPill ok={!!sectionStatus.red_flags} label="Red Flags" Icon={ShieldAlert} />
        <SectionStatusPill ok={!!sectionStatus.company_comparison} label="Peer Comparison" Icon={GitCompare} />
      </div>

      {/* Executive Summary */}
      {report.executive_summary && (
        <div className="bg-blue-50/40 rounded-xl p-5 border border-blue-100/80 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 flex items-center gap-1.5">
            <Sparkles size={14} className="text-blue-600" /> Executive Summary
          </h3>
          <p className="text-sm font-medium text-slate-700 leading-relaxed whitespace-pre-wrap">
            {report.executive_summary}
          </p>
        </div>
      )}

      {/* Outlook */}
      {report.outlook && (
        <div className="border-t border-slate-100 pt-5 space-y-2">
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span className="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">
              2
            </span>
            Outlook
          </h3>
          <p className="text-xs font-medium text-slate-600 leading-relaxed pl-8 whitespace-pre-wrap">
            {report.outlook}
          </p>
        </div>
      )}

      {/* Comparisons included */}
      {comparisons.length > 0 && (
        <div className="border-t border-slate-100 pt-5 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <GitCompare size={13} /> Comparisons Included
          </h3>
          <div className="flex flex-wrap gap-2">
            {comparisons.map((c) => (
              <span
                key={c.comparison_id}
                className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-[11px] font-bold"
              >
                {c.tickers.join(' vs ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer footer */}
      <div className="pt-6 border-t border-slate-200 text-center space-y-1">
        <p className="text-[11px] font-semibold text-slate-400">
          All financial data, ratios, and risk flags are drawn directly from the linked company document.
          Full financial tables, risk detail, and comparison charts are included in the downloaded PDF.
        </p>
        <p className="text-[10px] text-slate-400">
          Generated via Multi-Agent Financial Research System &middot; Report Agent
        </p>
      </div>
    </div>
  )
}

export default ReportPreview