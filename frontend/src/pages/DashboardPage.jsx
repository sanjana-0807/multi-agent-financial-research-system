import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'

import WorkspaceCard from '../features/workspace/WorkspaceCard.jsx'
import CreateWorkspaceModal from '../features/workspace/CreateWorkspaceModal.jsx'
import useWorkspaces from '../features/workspace/useWorkspaces.js'
import Loader from '../components/Loader.jsx'
import { useWorkspace } from '../context/WorkspaceContext.jsx'

function DashboardPage() {
  const navigate = useNavigate()

  // Get the active workspace setter from the global workspace context.
  // WorkspaceDetailPage uses this same context to know which workspace
  // is currently selected.
  const { setActiveWorkspace } = useWorkspace()

  const {
    workspaces,
    loading,
    error,
    createWorkspace,
  } = useWorkspaces()

  const [showCreate, setShowCreate] = useState(false)

  // Loading state
  if (loading) {
    return <Loader text="Loading sessions..." />
  }

  return (
    <div className="p-6">
      {/* =========================================================
          HEADER
      ========================================================== */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Dashboard
          </h1>

          <p className="text-gray-500">
            Your research sessions
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          New Session
        </button>
      </div>

      {/* =========================================================
          ERROR
      ========================================================== */}
      {error && (
        <p className="text-sm text-orange-500 mb-4">
          {error}
        </p>
      )}

      {/* =========================================================
          WORKSPACE LIST
      ========================================================== */}
      {workspaces.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 mb-4">
            No research sessions yet.
          </p>

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
            <WorkspaceCard
              key={ws.id || ws._id}
              workspace={ws}
              onClick={(workspace) => {
                const workspaceId =
                  workspace.id || workspace._id

                // IMPORTANT:
                // Set the selected workspace in WorkspaceContext
                // before opening the workspace detail page.
                setActiveWorkspace(workspace)

                // Open the workspace detail page.
                // WorkspaceDetailPage will show the Overview tab.
                navigate(
                  `/dashboard?workspace=${workspaceId}`
                )
              }}
            />
          ))}
        </div>
      )}

      {/* =========================================================
          CREATE WORKSPACE MODAL
      ========================================================== */}
      <CreateWorkspaceModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={createWorkspace}
      />
    </div>
  )
}

export default DashboardPage