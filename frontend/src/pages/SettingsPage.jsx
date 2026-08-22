import { useState } from 'react'
import {
  User, Lock, FolderKanban, Trash2, Edit3, Save, CheckCircle2,
  FileText, ShieldCheck, Plus, X, AlertTriangle, Sparkles
} from 'lucide-react'
import { useAuth } from '../features/auth/useAuth.js'
import { useWorkspace } from '../context/WorkspaceContext.jsx'
import Button from '../components/Button.jsx'

function SettingsPage() {
  const { user, updateUser } = useAuth()
  const { sessions, updateSession, deleteSession, deleteSessionDocument } = useWorkspace()

  // Profile Form State
  const [name, setName] = useState(user?.name || 'Charitha')
  const [email, setEmail] = useState(user?.email || 'charitha@ledgeriq.com')
  const [role, setRole] = useState(user?.role || 'Senior Financial Analyst')
  const [profileSaved, setProfileSaved] = useState(false)

  // Password Form State
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState(null)
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  // Session Management Modal State
  const [selectedSessionForDocs, setSelectedSessionForDocs] = useState(null)
  const [editingSession, setEditingSession] = useState(null)
  const [editSessionName, setEditSessionName] = useState('')
  const [editSessionDesc, setEditSessionDesc] = useState('')
  const [selectedDocIdsToDelete, setSelectedDocIdsToDelete] = useState([])

  // Save Profile
  function handleSaveProfile(e) {
    e.preventDefault()
    updateUser({ name, email, role })
    setProfileSaved(true)
    setTimeout(() => setProfileSaved(false), 2500)
  }

  // Update Password
  function handleUpdatePassword(e) {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(false)

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.')
      return
    }

    // Success
    setPasswordSuccess(true)
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
    setTimeout(() => setPasswordSuccess(false), 2500)
  }

  // Edit Session
  function startEditSession(session) {
    setEditingSession(session)
    setEditSessionName(session.name)
    setEditSessionDesc(session.objective || session.description || '')
  }

  function handleSaveEditSession(e) {
    e.preventDefault()
    if (!editingSession || !editSessionName.trim()) return
    updateSession(editingSession.id, {
      name: editSessionName.trim(),
      description: editSessionDesc.trim(),
      objective: editSessionDesc.trim()
    })
    setEditingSession(null)
  }

  // Manage Docs in Session
  function openDocManager(session) {
    setSelectedSessionForDocs(session)
    setSelectedDocIdsToDelete([])
  }

  function toggleDocSelection(docId) {
    setSelectedDocIdsToDelete((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    )
  }

  function handleDeleteSelectedDocs() {
    if (!selectedSessionForDocs) return
    selectedDocIdsToDelete.forEach((docId) => {
      deleteSessionDocument(selectedSessionForDocs.id, docId)
    })
    setSelectedDocIdsToDelete([])
    setSelectedSessionForDocs(null)
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8 animate-fadeIn select-none">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
          <Sparkles size={14} /> Workspace Preferences
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Account & Session Settings</h1>
        <p className="text-sm font-medium text-slate-500 mt-1">
          Manage your personal profile, security credentials, and research workspaces.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Profile & Security */}
        <div className="lg:col-span-6 space-y-6">
          {/* 1. Profile Editing */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <User size={20} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Profile Information</h3>
                <p className="text-xs text-slate-500">Update your analyst details and email</p>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Work Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Analyst Role / Title</label>
                <input
                  type="text"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-between">
                {profileSaved && (
                  <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 size={14} /> Profile Saved!
                  </span>
                )}
                <button
                  type="submit"
                  className="ml-auto flex items-center gap-1.5 bg-blue-600 text-white rounded-xl px-4 py-2 text-xs font-bold hover:bg-blue-700 transition-colors shadow-2xs"
                >
                  <Save size={14} /> Save Profile
                </button>
              </div>
            </form>
          </div>

          {/* 2. Password Editing */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-3d-subtle space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                <Lock size={20} />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Change Password</h3>
                <p className="text-xs text-slate-500">Ensure your account uses a strong password</p>
              </div>
            </div>

            <form onSubmit={handleUpdatePassword} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Current Password</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">New Password</label>
                <input
                  type="password"
                  placeholder="At least 8 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Confirm New Password</label>
                <input
                  type="password"
                  placeholder="Repeat new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {passwordError && (
                <p className="text-xs font-bold text-rose-500 flex items-center gap-1">
                  <AlertTriangle size={13} /> {passwordError}
                </p>
              )}

              <div className="pt-2 flex items-center justify-between">
                {passwordSuccess && (
                  <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                    <CheckCircle2 size={14} /> Password Updated!
                  </span>
                )}
                <button
                  type="submit"
                  className="ml-auto flex items-center gap-1.5 bg-slate-900 text-white rounded-xl px-4 py-2 text-xs font-bold hover:bg-slate-800 transition-colors shadow-2xs"
                >
                  <ShieldCheck size={14} /> Update Password
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Session & Document Management */}
        <div className="lg:col-span-6 space-y-6">
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
              <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
                {sessions.map((ws) => (
                  <div key={ws.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-900 truncate max-w-[200px]">{ws.name}</h4>
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
                    <div className="text-[10px] font-semibold text-slate-400 flex items-center justify-between pt-1 border-t border-slate-200/60">
                      <span>{ws.document_count || (ws.documents?.length || 0)} Disclosures Indexed</span>
                      <span>ID: {ws.id.slice(-6)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
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
              <button onClick={() => setSelectedSessionForDocs(null)} className="text-slate-400 hover:text-slate-700">
                <X size={16} />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Select the documents or indexed pages you wish to remove from this workspace session:
            </p>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {(!selectedSessionForDocs.documents || selectedSessionForDocs.documents.length === 0) ? (
                <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selectedDocIdsToDelete.includes('sample_doc')}
                      onChange={() => toggleDocSelection('sample_doc')}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="font-semibold text-slate-800">FY25_Annual_Report.pdf</span>
                  </div>
                  <span className="text-[10px] text-slate-400">186 pages · Indexed</span>
                </div>
              ) : (
                selectedSessionForDocs.documents.map((doc) => (
                  <div key={doc.id || doc.filename} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedDocIdsToDelete.includes(doc.id || doc.filename)}
                        onChange={() => toggleDocSelection(doc.id || doc.filename)}
                        className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="font-semibold text-slate-800">{doc.filename}</span>
                    </div>
                    <span className="text-[10px] text-slate-400">{doc.size || '2.4 MB'}</span>
                  </div>
                ))
              )}
            </div>

            <div className="flex gap-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedSessionForDocs(null)}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={selectedDocIdsToDelete.length === 0}
                onClick={handleDeleteSelectedDocs}
                className="flex-1 px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 disabled:opacity-50 transition-colors shadow-2xs"
              >
                Delete Selected ({selectedDocIdsToDelete.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SettingsPage
