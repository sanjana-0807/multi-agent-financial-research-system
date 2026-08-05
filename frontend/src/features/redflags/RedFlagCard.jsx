import { AlertTriangle } from 'lucide-react'
import SeverityBadge from './SeverityBadge.jsx'

// Displays a single red flag with severity badge, title, and description.
// Expected shape: { title, description, severity, category }
function RedFlagCard({ flag }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertTriangle size={18} className="text-red-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-gray-900 truncate">
              {flag.title || 'Unnamed Risk'}
            </h4>
            <SeverityBadge severity={flag.severity} />
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">
            {flag.description || 'No details available.'}
          </p>
          {flag.category && (
            <p className="text-xs text-gray-400 mt-2">Category: {flag.category}</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default RedFlagCard
