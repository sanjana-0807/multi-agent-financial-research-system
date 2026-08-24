import { createContext, useContext, useState, useEffect } from 'react'
import { AuthContext } from '../features/auth/AuthContext.jsx'
import { listWorkspaces, createWorkspace as apiCreateWorkspace, deleteWorkspace as apiDeleteWorkspace } from '../api/workspaceApi.js'
import { createCompany, listCompanies } from '../api/companiesApi.js'
import { getLatestDocumentForCompany } from '../api/documentsApi.js'
import { getExtraction } from '../api/extractionApi.js'
import { getRedFlagsForDocument } from '../api/redFlagsApi.js'

const WorkspaceContext = createContext(null)

export function WorkspaceProvider({ children }) {
  const auth = useContext(AuthContext)
  const isAuthenticated = auth?.isAuthenticated

  const [sessions, setSessions] = useState([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [activeWorkspace, setActiveWorkspaceState] = useState(null)
  const [companies, setCompanies] = useState([])       // all companies in active workspace
  const [activeCompany, setActiveCompany] = useState(null) // primary company for this session
  const [activeDocument, setActiveDocument] = useState(null)
  const [extractionData, setExtractionDataState] = useState(null)
  const [redFlagData, setRedFlagData] = useState(null)

  // Reset everything on logout / user change
  useEffect(() => {
    if (!isAuthenticated) {
      setSessions([])
      setActiveWorkspaceState(null)
      setCompanies([])
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)
    }
  }, [isAuthenticated])

  async function refreshSessions() {
    setSessionsLoading(true)
    try {
      const res = await listWorkspaces()
      setSessions(res.data)
    } finally {
      setSessionsLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) refreshSessions()
  }, [isAuthenticated])

  // Creates a workspace AND its primary company in one step, since the
  // backend requires every document to be linked to a Company that
  // belongs to a Workspace.
  async function createSession({ name, description, objective, companyName, ticker, industry, sector }) {
    const wsRes = await apiCreateWorkspace({ name, description, objective })
    const workspace = wsRes.data

    const companyRes = await createCompany({
      workspace_id: workspace.id,
      name: companyName,
      ticker,
      industry,
      sector,
    })
    const company = companyRes.data

    await refreshSessions()
    setActiveWorkspaceState(workspace)
    setCompanies([company])
    setActiveCompany(company)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    return { workspace, company }
  }

  async function deleteSession(workspaceId) {
    await apiDeleteWorkspace(workspaceId)
    await refreshSessions()
    if (activeWorkspace?.id === workspaceId) {
      setActiveWorkspaceState(null)
      setCompanies([])
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)
    }
  }

  // Opens an existing workspace: loads its companies, picks the first
  // as "active", and pulls its latest processed document + results if
  // one exists.
  async function setActiveWorkspace(workspace) {
    setActiveWorkspaceState(workspace)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    if (!workspace) {
      setCompanies([])
      setActiveCompany(null)
      return
    }

    const companiesRes = await listCompanies(workspace.id)
    const companyList = companiesRes.data
    setCompanies(companyList)

    const primary = companyList[0] || null
    setActiveCompany(primary)
    if (!primary) return

    try {
      const docRes = await getLatestDocumentForCompany(primary.id)
      const doc = docRes.data
      setActiveDocument(doc)

      if (doc.status === 'indexed' || doc.status === 'completed') {
        try {
          const extractionRes = await getExtraction(doc.document_id)
          setExtractionDataState(extractionRes.data)
        } catch {
          // extraction not available yet — fine, dashboard shows empty state
        }
        try {
          const flagsRes = await getRedFlagsForDocument(doc.document_id)
          setRedFlagData(flagsRes.data)
        } catch {
          // no red-flag run yet
        }
      }
    } catch {
      // 404 — no document linked to this company yet
      setActiveDocument(null)
    }
  }

  // Called by DocumentUpload after a successful upload + extraction +
  // red-flag run, so the dashboard has fresh data without a refetch.
  function setPipelineResults({ document, extraction, redFlags }) {
    setActiveDocument(document)
    setExtractionDataState(extraction)
    setRedFlagData(redFlags)
  }

  return (
    <WorkspaceContext.Provider
      value={{
        sessions,
        sessionsLoading,
        refreshSessions,
        createSession,
        deleteSession,
        activeWorkspace,
        setActiveWorkspace,
        companies,
        activeCompany,
        activeDocument,
        extractionData,
        redFlagData,
        setPipelineResults,
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