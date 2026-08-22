import { createContext, useContext, useState, useEffect, useRef } from 'react'
import { AuthContext } from '../features/auth/AuthContext.jsx'

const WorkspaceContext = createContext(null)

// Helper to get user-specific storage key
function getUserKey(user, key) {
  const email = (user?.email || 'guest').toLowerCase().trim()
  return `${key}_${email}`
}

function loadSaved(key, defaultValue = null) {
  try {
    const stored = localStorage.getItem(key)
    return stored ? JSON.parse(stored) : defaultValue
  } catch {
    return defaultValue
  }
}

export function WorkspaceProvider({ children }) {
  const auth = useContext(AuthContext)
  const user = auth?.user
  const userEmail = user?.email || 'guest'

  // Initialize state scoped to current user
  const [sessions, setSessions] = useState(() =>
    loadSaved(getUserKey(user, 'user_sessions'), [])
  )
  const [activeWorkspace, setActiveWorkspaceState] = useState(() =>
    loadSaved(getUserKey(user, 'active_workspace'), null)
  )
  const [documents, setDocuments] = useState([])
  const [activeDocumentId, setActiveDocumentId] = useState(null)
  const [extractionData, setExtractionDataState] = useState(() =>
    loadSaved(getUserKey(user, 'extractionData'), null)
  )
  const [uploadHistory, setUploadHistory] = useState(() =>
    loadSaved(getUserKey(user, 'uploadHistory'), [])
  )

  // Track previous user email to switch workspaces on login/logout
  const prevUserRef = useRef(userEmail)

  useEffect(() => {
    if (prevUserRef.current !== userEmail) {
      prevUserRef.current = userEmail
      // User changed (e.g. new login or logout) — load new user's isolated workspace
      const newSessions = loadSaved(getUserKey(user, 'user_sessions'), [])
      const newUploads = loadSaved(getUserKey(user, 'uploadHistory'), [])
      const newExtraction = loadSaved(getUserKey(user, 'extractionData'), null)
      const newWorkspace = loadSaved(getUserKey(user, 'active_workspace'), null)

      setSessions(newSessions)
      setUploadHistory(newUploads)
      setExtractionDataState(newExtraction)
      setActiveWorkspaceState(newWorkspace)
      setDocuments([])
      setActiveDocumentId(null)
    }
  }, [userEmail, user])

  // Persist sessions for current user
  useEffect(() => {
    localStorage.setItem(getUserKey(user, 'user_sessions'), JSON.stringify(sessions))
  }, [sessions, user])

  // Persist active workspace for current user
  useEffect(() => {
    const key = getUserKey(user, 'active_workspace')
    if (activeWorkspace) {
      localStorage.setItem(key, JSON.stringify(activeWorkspace))
    } else {
      localStorage.removeItem(key)
    }
  }, [activeWorkspace, user])

  // Persist extraction data for current user
  useEffect(() => {
    const key = getUserKey(user, 'extractionData')
    if (extractionData) {
      localStorage.setItem(key, JSON.stringify(extractionData))
    } else {
      localStorage.removeItem(key)
    }
  }, [extractionData, user])

  // Persist upload history for current user
  useEffect(() => {
    localStorage.setItem(getUserKey(user, 'uploadHistory'), JSON.stringify(uploadHistory))
  }, [uploadHistory, user])

  // Set active workspace and sync its isolated extraction data
  function setActiveWorkspace(ws) {
    setActiveWorkspaceState(ws)
    if (!ws) {
      setExtractionDataState(null)
      return
    }
    // If the session has its own verified extraction data, load it; otherwise null
    setExtractionDataState(ws.extractionData || null)
  }

  // Create a new session — completely empty, NO default data!
  function createSession(sessionData) {
    const newSession = {
      id: String(Date.now()),
      name: sessionData.name || 'Untitled Research Session',
      description: sessionData.description || '',
      objective: sessionData.objective || sessionData.description || '',
      document_count: 0,
      documents: [],
      extractionData: null,
      created_at: new Date().toISOString()
    }
    setSessions((prev) => [newSession, ...prev])
    setActiveWorkspaceState(newSession)
    setExtractionDataState(null) // Brand new session starts completely empty!
    return newSession
  }

  // Update an existing session
  function updateSession(sessionId, updatedFields) {
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, ...updatedFields } : s))
    )
    if (activeWorkspace && activeWorkspace.id === sessionId) {
      setActiveWorkspaceState((prev) => ({ ...prev, ...updatedFields }))
    }
  }

  // Delete a session
  function deleteSession(sessionId) {
    setSessions((prev) => prev.filter((s) => s.id !== sessionId))
    if (activeWorkspace && activeWorkspace.id === sessionId) {
      setActiveWorkspaceState(null)
      setExtractionDataState(null)
    }
  }

  // Delete specific documents in a session
  function deleteSessionDocument(sessionId, documentId) {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === sessionId) {
          const updatedDocs = (s.documents || []).filter((d) => d.id !== documentId && d.filename !== documentId)
          return {
            ...s,
            documents: updatedDocs,
            document_count: updatedDocs.length,
            extractionData: updatedDocs.length === 0 ? null : s.extractionData
          }
        }
        return s
      })
    )
    setUploadHistory((prev) => prev.filter((d) => d.id !== documentId && d.filename !== documentId))
    if (activeWorkspace && activeWorkspace.id === sessionId) {
      const remainingDocs = (activeWorkspace.documents || []).filter((d) => d.id !== documentId && d.filename !== documentId)
      if (remainingDocs.length === 0) {
        setExtractionDataState(null)
      }
    }
  }

  // Set extraction data globally and attach to active session
  function setExtractionData(data) {
    setExtractionDataState(data)
    if (data?.document_id) {
      setActiveDocumentId(data.document_id)
    }
    if (activeWorkspace) {
      updateSession(activeWorkspace.id, {
        extractionData: data,
        document_count: Math.max(activeWorkspace.document_count || 0, 1)
      })
    }
  }

  // Add uploaded document
  function addUploadedDocument(doc) {
    setUploadHistory((prev) => {
      const filtered = prev.filter((d) => d.filename !== doc.filename)
      return [doc, ...filtered]
    })
    if (activeWorkspace) {
      const currentDocs = activeWorkspace.documents || []
      const updatedDocs = [doc, ...currentDocs.filter((d) => d.filename !== doc.filename)]
      updateSession(activeWorkspace.id, {
        documents: updatedDocs,
        document_count: updatedDocs.length
      })
    }
  }

  // Update status of document in history
  function updateDocumentStatus(filename, status) {
    setUploadHistory((prev) =>
      prev.map((d) => (d.filename === filename ? { ...d, status } : d))
    )
  }

  const clearWorkspace = () => {
    setActiveWorkspaceState(null)
    setDocuments([])
    setActiveDocumentId(null)
    setExtractionDataState(null)
    localStorage.removeItem('extractionData')
  }

  return (
    <WorkspaceContext.Provider
      value={{
        sessions,
        setSessions,
        createSession,
        updateSession,
        deleteSession,
        deleteSessionDocument,
        activeWorkspace,
        setActiveWorkspace,
        documents,
        setDocuments,
        activeDocumentId,
        setActiveDocumentId,
        extractionData,
        setExtractionData,
        uploadHistory,
        addUploadedDocument,
        updateDocumentStatus,
        clearWorkspace,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext)
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return context
}
