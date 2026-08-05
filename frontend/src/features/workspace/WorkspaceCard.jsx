import { Briefcase, FileText, Clock } from 'lucide-react'
import { formatDate } from '../../utils/formatDate.js'

function WorkspaceCard({ workspace, onClick }) {
  return (
    <div
      onClick={() => onClick?.(workspace)}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
          <Briefcase size={20} className="text-blue-600" />
        </div>
      </div>

      <h3 className="text-sm font-semibold text-gray-900 mb-1">
        {workspace.name || 'Untitled Session'}
      </h3>
      <p className="text-xs text-gray-500 mb-3 line-clamp-2">
        {workspace.description || 'No description'}
      </p>

      <div className="flex items-center gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <FileText size={12} />
          {workspace.document_count ?? 0} docs
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} />
          {formatDate(workspace.created_at)}
        </span>
      </div>
    </div>
  )
}

export default WorkspaceCard
