import { useState, useEffect } from 'react'
import WorkspaceCard from './WorkspaceCard.jsx'
import CreateWorkspaceModal from './CreateWorkspaceModal.jsx'
import Button from '../../components/Button.jsx'
import { Plus, Search, FolderKanban, FileText, Cpu, Sparkles, Inbox } from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

function loadSavedSessions() {
  try {
    const saved = localStorage.getItem('user_sessions')
    return saved ? JSON.parse(saved) : []
  } catch {
    return []
  }
}

function WorkspaceList() {
  const { extractionData, uploadHistory } = useWorkspace()
  const [sessions, setSessions] = useState(() => {
    const saved = loadSavedSessions()
    if (saved.length > 0) return saved
    if (extractionData && extractionData.company) {
      return [{
        id: 'active_session',
        name: `${extractionData.company} FY ${extractionData.fiscal_year || 2025} Analysis`,
        description: `Financial extraction and multi-agent research session for ${extractionData.company}.`,
        document_count: uploadHistory.length || 1,
        created_at: new Date().toISOString()
      }]
    }
    return []
  })
  const [modalOpen, setModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('user_sessions', JSON.stringify(sessions))
    }
  }, [sessions])

  function handleCreate(data) {
    const newSession = {
      id: String(Date.now()),
      name: data.name,
      description: data.description,
      document_count: 0,
      created_at: new Date().toISOString()
    }
    setSessions(prev => [newSession, ...prev])
  }

  const filteredSessions = sessions.filter(s => 
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totalDocs = uploadHistory.length || sessions.reduce((acc, curr) => acc + (curr.document_count || 0), 0)

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Session Workspace
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Research Sessions</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Manage multi-agent analysis workspaces, company filings, and research reports.
          </p>
        </div>

        <Button
          onClick={() => setModalOpen(true)}
          icon={Plus}
          variant="primary"
          size="md"
        >
          New Session
        </Button>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-3d-subtle flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <FolderKanban size={22} />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Sessions</div>
            <div className="text-2xl font-extrabold text-slate-900">{sessions.length}</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-3d-subtle flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <FileText size={22} />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Ingested Filings</div>
            <div className="text-2xl font-extrabold text-slate-900">{totalDocs} PDFs</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-3d-subtle flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Cpu size={22} />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Agent Engine</div>
            <div className="text-sm font-bold text-emerald-600 flex items-center gap-1 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Ready & Online
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3 bg-white rounded-2xl p-4 border border-slate-200/80 shadow-3d-subtle">
        <Search size={18} className="text-slate-400 ml-1" />
        <input
          type="text"
          placeholder="Search sessions by company name or report description..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full text-sm font-medium text-slate-800 placeholder-slate-400 bg-transparent outline-none"
        />
        {searchTerm && (
          <button 
            onClick={() => setSearchTerm('')}
            className="text-xs font-bold text-slate-400 hover:text-slate-700 px-2 py-1 bg-slate-100 rounded-lg"
          >
            Clear
          </button>
        )}
      </div>

      {/* Sessions Content */}
      {filteredSessions.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <Inbox size={24} />
          </div>
          <h3 className="text-base font-bold text-slate-800">No research sessions yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Create a new session or upload a financial filing to start automated research analysis.
          </p>
          <Button onClick={() => setModalOpen(true)} icon={Plus} variant="outline" size="sm" className="mt-2">
            Create Session
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSessions.map((ws) => (
            <WorkspaceCard key={ws.id} workspace={ws} onClick={() => {}} />
          ))}
        </div>
      )}

      {/* New Session Modal */}
      <CreateWorkspaceModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}

export default WorkspaceList
