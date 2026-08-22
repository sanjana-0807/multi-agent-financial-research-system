import { CheckCircle, AlertTriangle, BarChart3, FileText } from 'lucide-react'
import CitationTag from './CitationTag.jsx'
import Badge from '../../components/Badge.jsx'

// Container showing all agent outputs after a research job completes.
// Receives the consolidated result object from useResearchJob.
function ResearchResults({ result }) {
  if (!result) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        Submit a research prompt to see results here.
      </div>
    )
  }

  const { extraction, red_flags, comparison, summary, citations } = result

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      {summary && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <FileText size={18} className="text-blue-600" />
            <h3 className="text-sm font-semibold text-gray-900">Research Summary</h3>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{summary}</p>
          {citations && citations.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {citations.map((cite, i) => (
                <CitationTag key={i} source={cite.source} page={cite.page} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Extraction Results */}
      {extraction && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 size={18} className="text-green-600" />
            <h3 className="text-sm font-semibold text-gray-900">Extracted Metrics</h3>
            <Badge variant="success">Completed</Badge>
          </div>
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto">
            {JSON.stringify(extraction, null, 2)}
          </pre>
        </div>
      )}

      {/* Red Flags */}
      {red_flags && red_flags.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={18} className="text-orange-500" />
            <h3 className="text-sm font-semibold text-gray-900">Red Flags</h3>
            <Badge variant="warning">{red_flags.length} found</Badge>
          </div>
          <ul className="space-y-2">
            {red_flags.map((flag, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <AlertTriangle size={14} className="text-orange-400 mt-0.5 flex-shrink-0" />
                {flag.description || flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Comparison */}
      {comparison && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle size={18} className="text-purple-600" />
            <h3 className="text-sm font-semibold text-gray-900">Comparison</h3>
          </div>
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto">
            {JSON.stringify(comparison, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default ResearchResults
