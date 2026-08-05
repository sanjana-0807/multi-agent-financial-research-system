import { useState } from 'react'
import { Plus } from 'lucide-react'
import WorkspaceCard from '../features/workspace/WorkspaceCard.jsx'
import CreateWorkspaceModal from '../features/workspace/CreateWorkspaceModal.jsx'
import useWorkspaces from '../features/workspace/useWorkspaces.js'
import Loader from '../components/Loader.jsx'

// Dashboard = workspace overview. Shows all research sessions with a "New Session" button.
function DashboardPage() {
  const { workspaces, loading, error, createWorkspace } = useWorkspaces()
  const [showCreate, setShowCreate] = useState(false)

  if (loading) return <Loader text="Loading sessions..." />

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Your research sessions</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          New Session
        </button>
      </div>

      {error && <p className="text-sm text-orange-500 mb-4">{error}</p>}

      {workspaces.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 mb-4">No research sessions yet.</p>
          <button
            onClick={() => setShowCreate(true)}
            className="text-blue-600 text-sm font-medium hover:underline"
          >
            Create your first session
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <WorkspaceCard key={ws.id || ws._id} workspace={ws} onClick={() => {}} />
          ))}
        </div>
      )}

      <CreateWorkspaceModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={createWorkspace}
      />
    </div>
  )
}

export default DashboardPage
