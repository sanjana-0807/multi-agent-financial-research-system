import { FileText } from 'lucide-react'
import Badge from '../../components/Badge.jsx'

// Displays a preview of the generated report content.
// Expected shape: report = { title, summary, sections: [{ heading, content }], generated_at }
function ReportPreview({ report }) {
  if (!report) {
    return (
      <div className="text-center py-10">
        <FileText size={32} className="text-gray-300 mx-auto mb-2" />
        <p className="text-sm text-gray-400">No report generated yet. Run an analysis first.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">{report.title || 'Financial Report'}</h2>
          {report.generated_at && (
            <p className="text-xs text-gray-400 mt-1">Generated: {report.generated_at}</p>
          )}
        </div>
        <Badge variant="success">Ready</Badge>
      </div>

      {report.summary && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Executive Summary</h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{report.summary}</p>
        </div>
      )}

      {report.sections && report.sections.length > 0 && (
        <div className="space-y-5">
          {report.sections.map((section, i) => (
            <div key={i} className="border-t border-gray-100 pt-4">
              <h3 className="text-sm font-semibold text-gray-800 mb-2">{section.heading}</h3>
              <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{section.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ReportPreview
