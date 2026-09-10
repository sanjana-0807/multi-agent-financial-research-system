import { useWorkspace } from '../context/WorkspaceContext.jsx'
import useReportGeneration from '../features/report/useReportGeneration.js'
import ReportPreview from '../features/report/ReportPreview.jsx'
import ReportExportButton from '../features/report/ReportExportButton.jsx'
import { FileText, Sparkles } from 'lucide-react'
import Button from '../components/Button.jsx'

function ReportPage({ comparisonResult }) {
  const { activeWorkspace, activeDocument, extractionData } = useWorkspace()

  const {
    generate,
    reportId,
    report,
    loading,
    error,
  } = useReportGeneration()

  const company =
    extractionData?.company ||
    activeWorkspace?.name ||
    'Company Financial Review'

  const year = extractionData?.fiscal_year || 2025

  const hasDocument = Boolean(activeDocument?.document_id)

  const hasComparison = Boolean(comparisonResult?.id)

  async function handleGenerateReport() {
    if (!activeDocument?.document_id) return

    await generate(
      activeDocument.document_id,
      comparisonResult?.id || null
    )
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6 animate-fadeIn select-none">

      {/* Report Configuration */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle space-y-4 no-print">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">

          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
              <Sparkles size={14} />
              Report Agent Synthesis
            </div>

            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Executive Research Report
            </h1>

            <p className="text-sm font-medium text-slate-500 mt-1">
              Generate the final financial research report from the processed company disclosure.
            </p>

            {activeDocument?.document_id && (
              <p className="text-xs text-slate-400 mt-2">
                Document: {activeDocument.document_id}
              </p>
            )}

            {hasComparison && (
              <p className="text-xs text-emerald-600 mt-2">
                Comparison result ready and will be included in the report.
              </p>
            )}

            {!hasComparison && (
              <p className="text-xs text-slate-400 mt-2">
                Run a company comparison first to include the Company Comparison section.
              </p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleGenerateReport}
              disabled={!hasDocument || loading}
              icon={FileText}
              variant="primary"
              size="sm"
            >
              {loading ? 'Generating...' : 'Generate Report'}
            </Button>

            {reportId && report && (
              <ReportExportButton
                reportId={reportId}
                filename={`${company.replace(/\s+/g, '_')}_Financial_Report_FY${year}.pdf`}
              />
            )}
          </div>
        </div>

        {loading && (
          <div className="pt-3 border-t border-slate-100 text-sm font-medium text-blue-600">
            Report Agent is generating the report. Please wait...
          </div>
        )}

        {error && (
          <div className="pt-3 border-t border-slate-100 text-sm font-medium text-red-600">
            {error}
          </div>
        )}

        {!hasDocument && (
          <div className="pt-3 border-t border-slate-100 text-sm font-medium text-slate-500">
            Upload and process a financial document before generating a report.
          </div>
        )}
      </div>

      {/* Generated Report */}
      <ReportPreview report={report} />

    </div>
  )
}

export default ReportPage