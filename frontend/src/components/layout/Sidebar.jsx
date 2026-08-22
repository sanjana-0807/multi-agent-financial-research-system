import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Upload, FolderKanban, Plus,
  FileText, Settings as SettingsIcon, ChevronRight, Sparkles, Database
} from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'
import CreateWorkspaceModal from '../../features/workspace/CreateWorkspaceModal.jsx'

function Sidebar() {
  const { sessions, activeWorkspace, setActiveWorkspace, createSession } = useWorkspace()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const navigate = useNavigate()

  function handleCreate(data) {
    const newSession = createSession(data)
    setActiveWorkspace(newSession)
    setShowCreateModal(false)
    navigate('/upload')
  }

  function handleSwitchSession(session) {
    setActiveWorkspace(session)
    if (session.document_count > 0 || session.extractionData) {
      navigate('/dashboard')
    } else {
      navigate('/upload')
    }
  }

  return (
    <aside className="w-64 bg-white text-slate-700 flex flex-col h-screen sticky top-0 z-30 select-none border-r border-slate-200/80 shadow-3d-subtle">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-blue-600 text-white font-black text-base flex items-center justify-center shadow-md shadow-blue-500/20">
            ⌁
          </div>
          <div>
            <h1 className="font-extrabold text-slate-900 text-sm tracking-tight leading-none">Multi-Agent AI</h1>
            <p className="text-[10px] font-semibold text-slate-400 mt-0.5">Financial Research</p>
          </div>
        </div>
      </div>

      {/* Main Navigation Links */}
      <div className="px-3 pt-4 space-y-1">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              isActive
                ? 'bg-blue-50 text-blue-600 border border-blue-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`
          }
        >
          <div className="flex items-center gap-2.5">
            <LayoutDashboard size={16} className="text-blue-600" />
            <span>Overview Dashboard</span>
          </div>
          <ChevronRight size={13} className="text-slate-400" />
        </NavLink>

        <NavLink
          to="/upload"
          className={({ isActive }) =>
            `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              isActive
                ? 'bg-blue-50 text-blue-600 border border-blue-200/80 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`
          }
        >
          <div className="flex items-center gap-2.5">
            <Upload size={16} className="text-blue-600" />
            <span>Upload Disclosures</span>
          </div>
          <ChevronRight size={13} className="text-slate-400" />
        </NavLink>
      </div>

      {/* SESSIONS SECTION (Matching index.html) */}
      <div className="flex-1 px-3 pt-5 pb-2 overflow-y-auto custom-scrollbar flex flex-col">
        <div className="px-2 pb-2 text-[10px] font-extrabold uppercase tracking-widest text-slate-400 flex items-center justify-between">
          <span>YOUR SESSIONS</span>
          <span className="text-slate-500 font-bold px-1.5 py-0.2 bg-slate-100 rounded text-[9px]">{sessions.length}</span>
        </div>

        <div className="space-y-1 flex-1">
          {sessions.length === 0 ? (
            <div className="p-3 text-center rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-400">
              No sessions yet.
            </div>
          ) : (
            sessions.map((s) => {
              const isSelected = activeWorkspace?.id === s.id
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => handleSwitchSession(s)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-xl text-xs text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-50 border border-blue-200 text-blue-700 font-bold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-blue-600 animate-pulse' : 'bg-slate-300'}`} />
                    <span className="truncate">{s.name}</span>
                  </div>
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-white text-slate-500 border border-slate-200">
                    {s.document_count || (s.documents?.length || 0)}
                  </span>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Bottom Actions: Create Session & Settings */}
      <div className="p-3 border-t border-slate-100 space-y-1.5 bg-slate-50/50">
        <button
          type="button"
          onClick={() => setShowCreateModal(true)}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl border border-dashed border-slate-300 hover:border-blue-500 text-xs font-bold text-slate-700 hover:text-blue-700 bg-white hover:bg-blue-50/40 transition-all cursor-pointer shadow-2xs"
        >
          <Plus size={14} className="text-blue-600" />
          <span>＋ Create New Session</span>
        </button>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
              isActive
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`
          }
        >
          <SettingsIcon size={14} className="text-slate-400" />
          <span>Settings & Preferences</span>
        </NavLink>
      </div>

      {/* Modal for creating new session */}
      <CreateWorkspaceModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />
    </aside>
  )
}

export default Sidebar
