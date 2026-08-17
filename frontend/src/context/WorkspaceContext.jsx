import { createContext, useContext, useState, useEffect } from 'react'

const WorkspaceContext = createContext(null)

// Load upload history from localStorage
function loadUploadHistory() {
  try {
    const stored = localStorage.getItem('uploadHistory')
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// Load last extraction data from localStorage
function loadExtractionData() {
  try {
    const stored = localStorage.getItem('extractionData')
    if (!stored) return null
    const parsed = JSON.parse(stored)
    // Clear stale old test data if company is Tesla
    if (parsed && (parsed.company === 'Tesla Inc.' || parsed.revenue === 879891)) {
      localStorage.removeItem('extractionData')
      return null
    }
    return parsed
  } catch {
    return null
  }
}

// Tracks the currently active workspace session and its associated documents.
// Any component can read/set the active workspace without prop drilling.
export function WorkspaceProvider({ children }) {
  const [activeWorkspace, setActiveWorkspace] = useState(null)
  const [documents, setDocuments] = useState([])
  const [activeDocumentId, setActiveDocumentId] = useState(null)
  const [extractionData, setExtractionDataState] = useState(loadExtractionData)
  const [uploadHistory, setUploadHistory] = useState(loadUploadHistory)

  // Persist extraction data to localStorage whenever it changes
  useEffect(() => {
    if (extractionData) {
      localStorage.setItem('extractionData', JSON.stringify(extractionData))
    }
  }, [extractionData])

  // Persist upload history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('uploadHistory', JSON.stringify(uploadHistory))
  }, [uploadHistory])

  // Set extraction data globally (called after API response)
  function setExtractionData(data) {
    setExtractionDataState(data)
    if (data?.document_id) {
      setActiveDocumentId(data.document_id)
    }
  }

  // Add a newly uploaded document to history
  function addUploadedDocument(doc) {
    setUploadHistory((prev) => {
      // Avoid duplicates by filename
      const filtered = prev.filter((d) => d.filename !== doc.filename)
      return [doc, ...filtered]
    })
  }

  // Update status of a document in upload history
  function updateDocumentStatus(filename, status) {
    setUploadHistory((prev) =>
      prev.map((d) => (d.filename === filename ? { ...d, status } : d))
    )
  }

  const clearWorkspace = () => {
    setActiveWorkspace(null)
    setDocuments([])
    setActiveDocumentId(null)
    setExtractionDataState(null)
    localStorage.removeItem('extractionData')
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
  const ctx = useContext(WorkspaceContext)
  if (!ctx) throw new Error('useWorkspace must be used inside a WorkspaceProvider')
  return ctx
}

export default WorkspaceContext
