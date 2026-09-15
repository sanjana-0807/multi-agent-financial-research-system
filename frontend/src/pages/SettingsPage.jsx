import { useState } from 'react'
import {
  FolderKanban, Trash2, Edit3, FileText, X, Sparkles, Loader2
} from 'lucide-react'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

function SettingsPage() {
  const { sessions, updateSession, deleteSession, getSessionDocuments, deleteSessionDocument } = useWorkspace()

  // Session Management Modal State
  const [selectedSessionForDocs, setSelectedSessionForDocs] = useState(null)
  const [docsLoading, setDocsLoading] = useState(false)
  const [editingSession, setEditingSession] = useState(null)
  const [editSessionName, setEditSessionName] = useState('')
  const [editSessionDesc, setEditSessionDesc] = useState('')
  const [selectedDocIdsToDelete, setSelectedDocIdsToDelete] = useState([])
  const [deletingDocs, setDeletingDocs] = useState(false)

  // Edit Session
  function startEditSession(session) {
    setEditingSession(session)
    setEditSessionName(session.name)
    setEditSessionDesc(session.objective || session.description || '')
  }

  async function handleSaveEditSession(e) {
    e.preventDefault()
    if (!editingSession || !editSessionName.trim()) return
    await updateSession(editingSession.id, {
      name: editSessionName.trim(),
      description: editSessionDesc.trim(),
      objective: editSessionDesc.trim()
    })
    setEditingSession(null)
  }

  // Manage Docs in Session
  async function openDocManager(session) {
    setSelectedDocIdsToDelete([])
    setSelectedSessionForDocs(session)
    setDocsLoading(true)
    try {
      const documents = await getSessionDocuments(session.id)
      setSelectedSessionForDocs({ ...session, documents })
    } catch (err) {
      console.error('Failed to load session documents:', err)
      setSelectedSessionForDocs({ ...session, documents: [] })
    } finally {
      setDocsLoading(false)
    }
  }

  function closeDocManager() {
    setSelectedSessionForDocs(null)
    setSelectedDocIdsToDelete([])
  }

  function toggleDocSelection(docId) {
    setSelectedDocIdsToDelete((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  async function handleDeleteSelectedDocs() {
    if (!selectedSessionForDocs || selectedDocIdsToDelete.length === 0) return

    setDeletingDocs(true)
    try {
      await Promise.all(
        selectedDocIdsToDelete.map((docId) =>
          deleteSessionDocument(selectedSessionForDocs.id, docId)
        )
      )
    } catch (err) {
      console.error('Failed to delete one or more documents:', err)
    } finally {
      setDeletingDocs(false)
      setSelectedDocIdsToDelete([])
      closeDocManager()
    }
  }

  return (
    <div className="p-6 md:p-8 max-w-3xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
          <Sparkles size={14} /> Workspace Preferences
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Session Settings</h1>
        <p className="text-sm font-medium text-slate-500 mt-1">
          Manage your research workspaces and indexed filings.
        </p>
      </div>

      {/* Session & Document Management */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
              <FolderKanban size={20} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Manage Sessions</h3>
              <p className="text-xs text-slate-500">Edit or delete workspaces and indexed filings</p>
            </div>
          </div>
          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
            {sessions.length} Workspaces
          </span>
        </div>

        {sessions.length === 0 ? (
          <p className="text-xs text-slate-400 py-6 text-center">No active research sessions found.</p>
        ) : (
          <div className="space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {sessions.map((ws) => (
              <div key={ws.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-900 truncate max-w-[280px]">{ws.name}</h4>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => startEditSession(ws)}
                      className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 transition-colors text-xs font-bold"
                      title="Rename / Edit Objective"
                    >
                      <Edit3 size={13} />
                    </button>
                    <button
                      type="button"
                      onClick={() => openDocManager(ws)}
                      className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-purple-600 hover:border-purple-300 transition-colors text-xs font-bold"
                      title="Manage Disclosures & Pages"
                    >
                      <FileText size={13} />
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteSession(ws.id)}
                      className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600 hover:text-rose-600 hover:border-rose-300 transition-colors text-xs font-bold"
                      title="Delete Session"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 line-clamp-1">
                  {ws.objective || ws.description || 'No objective specified.'}
                </p>
                <div className="text-[10px] font-semibold text-slate-400 flex items-center justify-end pt-1 border-t border-slate-200/60">
                  <span>ID: {ws.id.slice(-6)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Session Modal */}
      {editingSession && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-md w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Edit Research Session</h3>
              <button onClick={() => setEditingSession(null)} className="text-slate-400 hover:text-slate-700">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSaveEditSession} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Session Name</label>
                <input
                  type="text"
                  value={editSessionName}
                  onChange={(e) => setEditSessionName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Research Objective</label>
                <textarea
                  rows={3}
                  value={editSessionDesc}
                  onChange={(e) => setEditSessionDesc(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingSession(null)}
                  className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors shadow-2xs"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage / Delete Documents in Session Modal */}
      {selectedSessionForDocs && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-lg w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Manage Indexed Disclosures</h3>
                <p className="text-xs text-slate-500">Session: {selectedSessionForDocs.name}</p>
              </div>
              <button onClick={closeDocManager} className="text-slate-400 hover:text-slate-700">
                <X size={16} />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Select the documents you wish to remove from this workspace session:
            </p>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {docsLoading ? (
                <div className="flex items-center justify-center gap-2 py-8 text-xs text-slate-400">
                  <Loader2 size={16} className="animate-spin" />
                  Loading documents...
                </div>
              ) : !selectedSessionForDocs.documents || selectedSessionForDocs.documents.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">
                  No documents indexed for this session yet.
                </p>
              ) : (
                selectedSessionForDocs.documents.map((doc) => (
                  <div key={doc.document_id} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedDocIdsToDelete.includes(doc.document_id)}
                        onChange={() => toggleDocSelection(doc.document_id)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="font-semibold text-slate-800">{doc.filename}</span>
                    </div>
                    <span className="text-[10px] text-slate-400">{doc.page_count} pages · {doc.status}</span>
                  </div>
                ))
              )}
            </div>

            <div className="flex gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={closeDocManager}
                disabled={deletingDocs}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={selectedDocIdsToDelete.length === 0 || deletingDocs}
                onClick={handleDeleteSelectedDocs}
                className="flex-1 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 disabled:opacity-50 transition-colors shadow-2xs flex items-center justify-center gap-1.5"
              >
                {deletingDocs ? (
                  <>
                    <Loader2 size={13} className="animate-spin" /> Deleting...
                  </>
                ) : (
                  `Delete Selected (${selectedDocIdsToDelete.length})`
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SettingsPage