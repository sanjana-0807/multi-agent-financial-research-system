import { useState } from 'react'
import { FileText, Sparkles, Calendar, CheckCircle2, Award, Printer, Download, ArrowUpRight } from 'lucide-react'
import Badge from '../../components/Badge.jsx'
import Button from '../../components/Button.jsx'

function ReportPreview({ report }) {
  const [activeSection, setActiveSection] = useState(0)

  if (!report) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-3d-subtle">
        <FileText size={32} className="text-slate-300 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-400">No executive report generated yet. Run an analysis first.</p>
      </div>
    )
  }

  function handlePrint() {
    window.print()
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle p-8 space-y-6 select-none animate-fadeIn">
      {/* Official Report Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
            <Award size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600">
              <Sparkles size={12} /> Executive Research Report
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight mt-0.5">
              {report.title || 'Financial Disclosures Analysis'}
            </h2>
            {report.generated_at && (
              <p className="text-xs font-semibold text-slate-400 mt-1 flex items-center gap-1.5">
                <Calendar size={13} /> Generated on {report.generated_at}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="success">Verified Analysis</Badge>
          <Button onClick={handlePrint} icon={Printer} variant="outline" size="sm">
            Print PDF Report
          </Button>
        </div>
      </div>

      {/* Quick Section Navigation Bar */}
      {report.sections && report.sections.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-100">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex-shrink-0">Jump To:</span>
          <button
            onClick={() => setActiveSection(0)}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex-shrink-0 ${
              activeSection === 0 ? 'bg-blue-50 text-blue-600 border border-blue-200' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Executive Summary
          </button>
          {report.sections.map((sec, idx) => (
            <button
              key={idx}
              onClick={() => setActiveSection(idx + 1)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all flex-shrink-0 ${
                activeSection === idx + 1 ? 'bg-blue-50 text-blue-600 border border-blue-200' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {sec.heading}
            </button>
          ))}
        </div>
      )}

      {/* Executive Summary Card */}
      {report.summary && (
        <div className="bg-blue-50/40 rounded-xl p-5 border border-blue-100/80 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-wider text-blue-700 flex items-center gap-1.5">
            <Sparkles size={14} className="text-blue-600" /> Executive Summary
          </h3>
          <p className="text-sm font-medium text-slate-700 leading-relaxed whitespace-pre-wrap">
            {report.summary}
          </p>
        </div>
      )}

      {/* Report Detailed Sections */}
      {report.sections && report.sections.length > 0 && (
        <div className="space-y-6 pt-2">
          {report.sections.map((section, i) => (
            <div key={i} className="border-t border-slate-100 pt-5 space-y-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">
                  {i + 1}
                </span>
                {section.heading}
              </h3>
              <p className="text-sm font-medium text-slate-600 leading-relaxed whitespace-pre-wrap pl-8">
                {section.content}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Report Footer Verification Note */}
      <div className="pt-6 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400 font-semibold">
        <span className="flex items-center gap-1">
          <CheckCircle2 size={14} className="text-emerald-500" /> Multi-Agent AI System • Verified Disclosures
        </span>
        <span>Confidential Executive Analysis</span>
      </div>
    </div>
  )
}

export default ReportPreview


