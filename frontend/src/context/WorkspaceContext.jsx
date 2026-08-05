import { createContext, useContext, useState } from 'react'

const WorkspaceContext = createContext(null)

// Tracks the currently active workspace session and its associated documents.
// Any component can read/set the active workspace without prop drilling.
export function WorkspaceProvider({ children }) {
  const [activeWorkspace, setActiveWorkspace] = useState(null)
  const [documents, setDocuments] = useState([])
  const [activeDocumentId, setActiveDocumentId] = useState(null)

  const clearWorkspace = () => {
    setActiveWorkspace(null)
    setDocuments([])
    setActiveDocumentId(null)
  }

  return (
    <WorkspaceContext.Provider
      value={{
        activeWorkspace,
        setActiveWorkspace,
        documents,
        setDocuments,
        activeDocumentId,
        setActiveDocumentId,
        clearWorkspace,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace must be used inside a WorkspaceProvider')
  return ctx
}

export default WorkspaceContext
