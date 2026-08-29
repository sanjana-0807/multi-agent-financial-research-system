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
  const [activeCompany, setActiveCompany] = useState(null) // company whose data is currently shown
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

  // Creates a workspace only. Companies are added separately, inside
  // the workspace, right before a document is uploaded.
  async function createSession({ name, description, objective }) {
    const wsRes = await apiCreateWorkspace({ name, description, objective })
    const workspace = wsRes.data
    await refreshSessions()
    setActiveWorkspaceState(workspace)
    setCompanies([])
    setActiveCompany(null)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)
    return { workspace }
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

  // Re-fetches the company list for the active workspace. Call this
  // after adding a company or uploading a document so every tab
  // (Document, Comparison) sees the same up-to-date list instead of
  // each maintaining its own stale copy.
  async function refreshCompanies() {
    if (!activeWorkspace) return []
    const res = await listCompanies(activeWorkspace.id)
    setCompanies(res.data)
    return res.data
  }

  // Adds a company to the currently active workspace. Used inline on
  // the Upload page (first company) and now also reused for peer
  // companies added for comparison.
  async function addCompany({ name, ticker, industry, sector }) {
    if (!activeWorkspace) throw new Error('No active workspace')
    const res = await createCompany({
      workspace_id: activeWorkspace.id,
      name,
      ticker,
      industry,
      sector,
    })
    const company = res.data
    setCompanies((prev) => [...prev, company])
    if (!activeCompany) setActiveCompany(company)
    return company
  }

  // Fetches and loads a specific company's latest document, extraction,
  // and red-flag results into state. Returns true if a processed
  // document was found. This is the single source of truth used both
  // when opening a workspace (primary company) and when a user picks a
  // different company to view (e.g. from the Document tab).
  async function loadDataForCompany(company) {
    setActiveCompany(company)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    if (!company) return false

    try {
      const docRes = await getLatestDocumentForCompany(company.id)
      const doc = docRes.data
      setActiveDocument(doc)

      if (doc.status === 'indexed' || doc.status === 'completed') {
        try {
          const extractionRes = await getExtraction(doc.document_id)
          setExtractionDataState(extractionRes.data)
        } catch {}
        try {
  const flagsRes = await getRedFlagsForDocument(doc.document_id)
  // GET /red-flags/document/{id} returns a list (unlike POST /run,
  // which returns a single object) — unwrap it and take the latest.
  const flagsList = Array.isArray(flagsRes.data) ? flagsRes.data : [flagsRes.data]
  setRedFlagData(flagsList.length > 0 ? flagsList[flagsList.length - 1] : null)
} catch {}
        return true
      }
      return false
    } catch {
      setActiveDocument(null)
      return false
    }
  }

  // Switches which company's document/extraction/red-flag data is
  // shown as "active", fetching it fresh. Used by the Upload page's
  // company switcher and the Document tab's "view this company" click.
  async function selectCompany(company) {
    return loadDataForCompany(company)
  }

  // Opens an existing workspace: loads its companies, picks the first
  // as "active", and pulls its latest processed document + results if
  // one exists. Returns true if that primary company has processed data.
  async function setActiveWorkspace(workspace) {
    setActiveWorkspaceState(workspace)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    if (!workspace) {
      setCompanies([])
      setActiveCompany(null)
      return false
    }

    const companiesRes = await listCompanies(workspace.id)
    const companyList = companiesRes.data
    setCompanies(companyList)

    const primary = companyList[0] || null
    if (!primary) {
      setActiveCompany(null)
      return false
    }

    return loadDataForCompany(primary)
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
        refreshCompanies,
        activeCompany,
        addCompany,
        selectCompany,
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