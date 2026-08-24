import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import WorkspaceCard from './WorkspaceCard.jsx'
import CreateWorkspaceModal from './CreateWorkspaceModal.jsx'
import Button from '../../components/Button.jsx'
import {
  Plus, Search, FolderKanban, FileText, Sparkles, Inbox,
  ArrowRight, ArrowLeft, Database, Cpu, ShieldCheck, CheckCircle2, ChevronRight
} from 'lucide-react'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

const GUIDE_STEPS = [
  {
    step: '01',
    badge: 'Step 1 of 4',
    title: 'Name Your Research Workspace',
    desc: 'Create a private, dedicated workspace for a company, sector, or investment thesis (e.g., "Tesla FY25 Review" or "Banking Sector Matrix").',
    icon: FolderKanban,
    color: 'from-blue-600 to-indigo-600',
    tag: 'Workspace Setup'
  },
  {
    step: '02',
    badge: 'Step 2 of 4',
    title: 'Ingest Financial Disclosures',
    desc: 'Drag & drop 10-K, 10-Q filings, or annual earnings statements (PDF/DOCX) into the ingestion engine for automated chunking.',
    icon: Database,
    color: 'from-cyan-600 to-blue-600',
    tag: 'Document Ingestion'
  },
  {
    step: '03',
    badge: 'Step 3 of 4',
    title: '3-Agent Sequential Processing',
    desc: 'Document, Extraction, and Red Flag agents work in real-time to index ChromaDB embeddings, extract metrics, and scan auditor remarks.',
    icon: Cpu,
    color: 'from-indigo-600 to-purple-600',
    tag: 'Multi-Agent Pipeline'
  },
  {
    step: '04',
    badge: 'Step 4 of 4',
    title: 'Explore, Ask AI & Export Reports',
    desc: 'Maximize KPI cards, ask multi-part questions to the Research Agent, and compile a 5-section verified analyst PDF report.',
    icon: FileText,
    color: 'from-emerald-600 to-teal-600',
    tag: 'Analysis & Synthesis'
  }
]

function WorkspaceList() {
  const { sessions, createSession, deleteSession, setActiveWorkspace, uploadHistory } = useWorkspace()
  const [modalOpen, setModalOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)
  const navigate = useNavigate()

  // 3D Motion Step Auto-Looping Animation
  useEffect(() => {
    if (!isAutoPlaying) return
    const interval = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % GUIDE_STEPS.length)
    }, 3800)
    return () => clearInterval(interval)
  }, [isAutoPlaying])

  async function handleCreate(data) {
  const { workspace } = await createSession(data)
  setModalOpen(false)
  navigate('/upload')
}

async function handleOpenWorkspace(ws) {
  await setActiveWorkspace(ws)
  navigate(activeDocument ? '/dashboard' : '/upload')
}

  const currentStep = GUIDE_STEPS[currentStepIndex]
  const StepIcon = currentStep.icon

  const filteredSessions = sessions.filter(s => 
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (s.description && s.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (s.objective && s.objective.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* 3D Motion Looping Interactive Workflow Guide in Light Theme */}
      <div 
        onMouseEnter={() => setIsAutoPlaying(false)}
        onMouseLeave={() => setIsAutoPlaying(true)}
        className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 text-white rounded-3xl p-6 md:p-8 shadow-xl shadow-blue-500/15 perspective-1000 transition-all duration-500"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-white/20 text-white backdrop-blur-xs">
                Interactive Guided Workflow
              </span>
              <span className="text-xs text-blue-100 font-semibold">
                {currentStep.badge}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-xs border border-white/30 flex items-center justify-center text-white shadow-md transform transition-transform duration-500 hover:rotate-6">
                <StepIcon size={24} />
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white">
                {currentStep.title}
              </h2>
            </div>

            <p className="text-xs md:text-sm font-medium text-blue-50 leading-relaxed">
              {currentStep.desc}
            </p>

            {/* Step Progress Indicators & Manual Controls */}
            <div className="flex items-center gap-3 pt-2">
              {GUIDE_STEPS.map((s, idx) => (
                <button
                  key={s.step}
                  type="button"
                  onClick={() => setCurrentStepIndex(idx)}
                  className={`h-2 rounded-full transition-all duration-300 cursor-pointer ${
                    currentStepIndex === idx
                      ? 'w-8 bg-white'
                      : 'w-2 bg-white/30 hover:bg-white/60'
                  }`}
                  title={`Go to Step ${idx + 1}`}
                />
              ))}

              <div className="flex items-center gap-1.5 ml-4">
                <button
                  type="button"
                  onClick={() => setCurrentStepIndex((prev) => (prev === 0 ? GUIDE_STEPS.length - 1 : prev - 1))}
                  className="w-7 h-7 rounded-lg bg-white/20 hover:bg-white/30 text-white flex items-center justify-center text-xs transition-colors"
                >
                  <ArrowLeft size={13} />
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentStepIndex((prev) => (prev + 1) % GUIDE_STEPS.length)}
                  className="w-7 h-7 rounded-lg bg-white/20 hover:bg-white/30 text-white flex items-center justify-center text-xs transition-colors"
                >
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          </div>

          {/* Action Button & Stats Box */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 justify-center">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-white text-blue-700 font-extrabold text-sm hover:bg-blue-50 transition-all shadow-lg cursor-pointer"
            >
              <Plus size={16} />
              <span>Create Research Session</span>
            </button>
            <div className="p-3.5 bg-white/15 backdrop-blur-xs rounded-2xl border border-white/20 text-center">
              <span className="text-[10px] uppercase font-bold text-blue-100 tracking-wider block">Active Workspaces</span>
              <span className="text-xl font-extrabold text-white">{sessions.length} Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Page Heading & Search Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Workspace Directory
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Your Research Sessions</h1>
          <p className="text-xs font-medium text-slate-500 mt-1">
            Access previous analysis workspaces, upload additional disclosures, or inspect reports.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-72">
            <Search size={16} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search workspaces..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3.5 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
      </div>

      {/* Sessions Grid Content */}
      {filteredSessions.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center space-y-4 shadow-3d-subtle">
          <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
            <Inbox size={28} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800">No research sessions created yet</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              Click the button below to name your first research workspace and begin multi-agent extraction.
            </p>
          </div>
          <Button onClick={() => setModalOpen(true)} icon={Plus} variant="primary" size="md">
            Create First Session
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSessions.map((ws) => (
            <WorkspaceCard 
              key={ws.id} 
              workspace={ws} 
              onClick={handleOpenWorkspace}
              onDelete={deleteSession}
            />
          ))}
        </div>
      )}

      {/* Create Session Modal */}
      <CreateWorkspaceModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}

export default WorkspaceList
