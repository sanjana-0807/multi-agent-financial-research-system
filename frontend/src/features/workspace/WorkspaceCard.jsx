import { FolderKanban, FileText, Clock, ArrowRight, Sparkles, Trash2 } from 'lucide-react'
import { formatDate } from '../../utils/formatDate.js'

function WorkspaceCard({ workspace, onClick, onDelete }) {
  return (
    <div
      onClick={() => onClick?.(workspace)}
      className="group relative bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle shadow-3d-hover hover:border-blue-300 transition-all duration-300 p-5 cursor-pointer perspective-1000 select-none overflow-hidden"
    >
      {/* Top accent gradient line */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 opacity-70 group-hover:opacity-100 transition-opacity" />

      {/* Header Icon & Status Pill */}
      <div className="flex items-center justify-between mb-3.5">
        <div className="w-11 h-11 rounded-xl bg-blue-50/80 border border-blue-100 flex items-center justify-center text-blue-600 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-xs">
          <FolderKanban size={20} />
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/80">
            <Sparkles size={10} className="text-blue-500" /> Active Session
          </span>
          {onDelete && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                onDelete(workspace.id)
              }}
              className="text-slate-300 hover:text-rose-600 p-1 rounded-md hover:bg-rose-50 transition-colors"
              title="Delete session"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Title & Description */}
      <h3 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition-colors mb-1 tracking-tight truncate">
        {workspace.name || 'Untitled Research Session'}
      </h3>
      <p className="text-xs font-medium text-slate-500 mb-4 line-clamp-2 leading-relaxed">
        {workspace.objective || workspace.description || 'Comprehensive financial report and ratio analysis session.'}
      </p>

      {/* Metadata Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs font-semibold text-slate-400">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-slate-600">
            <FileText size={13} className="text-blue-500" />
            {workspace.document_count ?? (workspace.documents?.length || 0)} Disclosures
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Clock size={13} />
            {formatDate(workspace.created_at)}
          </span>
        </div>

        <div className="text-blue-600 group-hover:translate-x-1 transition-transform flex items-center gap-0.5 font-bold">
          <span>Open</span>
          <ArrowRight size={14} />
        </div>
      </div>
    </div>
  )
}

export default WorkspaceCard
