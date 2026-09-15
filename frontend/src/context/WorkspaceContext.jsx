import { createContext, useContext, useState, useEffect, useRef } from 'react'
import { AuthContext } from '../features/auth/AuthContext.jsx'
import {
  listWorkspaces,
  createWorkspace as apiCreateWorkspace,
  updateWorkspace as apiUpdateWorkspace,
  deleteWorkspace as apiDeleteWorkspace,
  getWorkspaceDocuments,
} from '../api/workspaceApi.js'
import { deleteDocument as apiDeleteDocument } from '../api/documentsApi.js'
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
  const [companies, setCompanies] = useState([])
  const [activeCompany, setActiveCompany] = useState(null)
  const [activeDocument, setActiveDocument] = useState(null)
  const [extractionData, setExtractionDataState] = useState(null)
  const [redFlagData, setRedFlagData] = useState(null)

  /*
   * Prevent duplicate workspace/company loading.
   *
   * This is important because the dashboard/sidebar can both attempt
   * to activate the same workspace while React is rendering.
   */
  const workspaceLoadRef = useRef(null)
  const loadedWorkspaceIdRef = useRef(null)

  const companyLoadRef = useRef(null)
  const loadedCompanyIdRef = useRef(null)

  // ---------------------------------------------------------
  // RESET ON LOGOUT
  // ---------------------------------------------------------

  useEffect(() => {
    if (!isAuthenticated) {
      setSessions([])
      setActiveWorkspaceState(null)
      setCompanies([])
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)

      workspaceLoadRef.current = null
      loadedWorkspaceIdRef.current = null
      companyLoadRef.current = null
      loadedCompanyIdRef.current = null
    }
  }, [isAuthenticated])

  // ---------------------------------------------------------
  // SESSIONS / WORKSPACES
  // ---------------------------------------------------------

  async function refreshSessions() {
    setSessionsLoading(true)

    try {
      const res = await listWorkspaces()
      setSessions(res.data)
      return res.data
    } finally {
      setSessionsLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      refreshSessions()
    }
  }, [isAuthenticated])

  async function createSession({ name, description, objective }) {
    const wsRes = await apiCreateWorkspace({
      name,
      description,
      objective,
    })

    const workspace = wsRes.data

    await refreshSessions()

    setActiveWorkspaceState(workspace)
    setCompanies([])
    setActiveCompany(null)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    workspaceLoadRef.current = null
    loadedWorkspaceIdRef.current = workspace.id || workspace._id || null
    companyLoadRef.current = null
    loadedCompanyIdRef.current = null

    return { workspace }
  }

  async function updateSession(workspaceId, updates) {
    const res = await apiUpdateWorkspace(workspaceId, updates)

    await refreshSessions()

    if (String(activeWorkspace?.id) === String(workspaceId)) {
      setActiveWorkspaceState(res.data)
    }

    return res.data
  }

  async function deleteSession(workspaceId) {
    await apiDeleteWorkspace(workspaceId)

    await refreshSessions()

    if (String(activeWorkspace?.id) === String(workspaceId)) {
      setActiveWorkspaceState(null)
      setCompanies([])
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)

      workspaceLoadRef.current = null
      loadedWorkspaceIdRef.current = null
      companyLoadRef.current = null
      loadedCompanyIdRef.current = null
    }
  }

  async function getSessionDocuments(workspaceId) {
    const res = await getWorkspaceDocuments(workspaceId)
    return res.data
  }

  async function deleteSessionDocument(workspaceId, documentId) {
    await apiDeleteDocument(documentId)
    await refreshSessions()
  }

  // ---------------------------------------------------------
  // COMPANIES
  // ---------------------------------------------------------

  async function refreshCompanies() {
    if (!activeWorkspace) return []

    const res = await listCompanies(activeWorkspace.id)
    const companyList = res.data || []

    setCompanies(companyList)

    return companyList
  }

  async function addCompany({ name, ticker, industry, sector }) {
    if (!activeWorkspace) {
      throw new Error('No active workspace')
    }

    const res = await createCompany({
      workspace_id: activeWorkspace.id,
      name,
      ticker,
      industry,
      sector,
    })

    const company = res.data

    setCompanies((prev) => {
      const exists = prev.some(
        (item) => String(item.id) === String(company.id)
      )

      if (exists) {
        return prev
      }

      return [...prev, company]
    })

    // Do not automatically select the newly added company.
    // The user should explicitly choose a company before its
    // document/extraction/red-flag data is loaded.

    return company
  }

  // ---------------------------------------------------------
  // LOAD COMPANY DATA
  // ---------------------------------------------------------

  async function loadDataForCompany(company, force = false) {
    if (!company) {
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)

      companyLoadRef.current = null
      loadedCompanyIdRef.current = null

      return false
    }

    const companyId = String(company.id)

    /*
     * If this exact company is already loaded and we are not
     * explicitly forcing a refresh, do nothing.
     */
    if (
      !force &&
      loadedCompanyIdRef.current === companyId &&
      companyLoadRef.current === null
    ) {
      setActiveCompany(company)
      return Boolean(activeDocument)
    }

    /*
     * If the same company is already being loaded, reuse the
     * existing promise instead of firing another API chain.
     */
    if (
      !force &&
      companyLoadRef.current?.companyId === companyId
    ) {
      return companyLoadRef.current.promise
    }

    setActiveCompany(company)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    const promise = (async () => {
      try {
        const docRes = await getLatestDocumentForCompany(companyId)
        const doc = docRes.data

        setActiveDocument(doc)

        if (
          doc.status !== 'indexed' &&
          doc.status !== 'completed'
        ) {
          loadedCompanyIdRef.current = companyId
          return false
        }

        /*
         * Extraction and red flags are independent.
         * Run them in parallel to reduce loading time.
         */
        const [extractionResult, flagsResult] =
          await Promise.allSettled([
            getExtraction(doc.document_id),
            getRedFlagsForDocument(doc.document_id),
          ])

        // -----------------------------
        // Extraction
        // -----------------------------

        if (extractionResult.status === 'fulfilled') {
          setExtractionDataState(
            extractionResult.value.data
          )
        } else {
          setExtractionDataState(null)
        }

        // -----------------------------
        // Red flags
        // -----------------------------

        if (flagsResult.status === 'fulfilled') {
          const rawFlags = flagsResult.value.data

          const flagsList = Array.isArray(rawFlags)
            ? rawFlags
            : rawFlags
              ? [rawFlags]
              : []

          setRedFlagData(
            flagsList.length > 0
              ? flagsList[flagsList.length - 1]
              : null
          )
        } else {
          setRedFlagData(null)
        }

        loadedCompanyIdRef.current = companyId

        return true
      } catch (error) {
        console.error(
          `Failed to load data for company ${companyId}:`,
          error
        )

        setActiveDocument(null)
        setExtractionDataState(null)
        setRedFlagData(null)

        return false
      } finally {
        /*
         * Only clear the ref if this is still the same request.
         */
        if (
          companyLoadRef.current?.companyId === companyId
        ) {
          companyLoadRef.current = null
        }
      }
    })()

    companyLoadRef.current = {
      companyId,
      promise,
    }

    return promise
  }

  // ---------------------------------------------------------
  // SELECT COMPANY
  // ---------------------------------------------------------

  async function selectCompany(company) {
    if (!company) {
      return loadDataForCompany(null)
    }

    /*
     * Selecting the company that is already active should not
     * refetch the document/extraction/red flags.
     */
    if (
      activeCompany &&
      String(activeCompany.id) === String(company.id) &&
      loadedCompanyIdRef.current === String(company.id) &&
      companyLoadRef.current === null
    ) {
      return true
    }

    return loadDataForCompany(company)
  }

  // ---------------------------------------------------------
  // OPEN WORKSPACE
  // ---------------------------------------------------------

  async function setActiveWorkspace(workspace) {
    if (!workspace) {
      setActiveWorkspaceState(null)
      setCompanies([])
      setActiveCompany(null)
      setActiveDocument(null)
      setExtractionDataState(null)
      setRedFlagData(null)

      workspaceLoadRef.current = null
      loadedWorkspaceIdRef.current = null
      companyLoadRef.current = null
      loadedCompanyIdRef.current = null

      return false
    }

    const workspaceId = String(
      workspace.id || workspace._id
    )

    /*
     * IMPORTANT USER FLOW:
     *
     * Selecting a session must NOT automatically select its first
     * company or load that company's document/extraction/red flags.
     *
     * The flow is:
     *
     *   Session
     *      ↓
     *   Companies in that session
     *      ↓
     *   User selects a company
     *      ↓
     *   loadDataForCompany(company)
     *      ↓
     *   Result / Overview
     */

    /*
     * If this workspace is already active and its companies have
     * already been loaded, do not fetch them again.
     *
     * Most importantly, do not automatically select a company.
     */
    if (
      loadedWorkspaceIdRef.current === workspaceId &&
      workspaceLoadRef.current === null
    ) {
      setActiveWorkspaceState(workspace)

      return false
    }

    /*
     * If the workspace is already being loaded, reuse the existing
     * request instead of starting another one.
     */
    if (
      workspaceLoadRef.current?.workspaceId === workspaceId
    ) {
      return workspaceLoadRef.current.promise
    }

    setActiveWorkspaceState(workspace)

    // A newly selected session starts with no selected company.
    setCompanies([])
    setActiveCompany(null)
    setActiveDocument(null)
    setExtractionDataState(null)
    setRedFlagData(null)

    loadedWorkspaceIdRef.current = null
    loadedCompanyIdRef.current = null
    companyLoadRef.current = null

    const promise = (async () => {
      try {
        const companiesRes =
          await listCompanies(workspaceId)

        const companyList = Array.isArray(companiesRes.data)
          ? companiesRes.data
          : []

        setCompanies(companyList)

        /*
         * DO NOT select companyList[0].
         *
         * The user must explicitly click a company.
         *
         * Returning false keeps the existing Sessions-page flow
         * on the company/upload screen rather than opening a
         * company result automatically.
         */
        setActiveCompany(null)
        setActiveDocument(null)
        setExtractionDataState(null)
        setRedFlagData(null)

        loadedWorkspaceIdRef.current = workspaceId

        return false
      } catch (error) {
        console.error(
          `Failed to open workspace ${workspaceId}:`,
          error
        )

        setCompanies([])
        setActiveCompany(null)
        setActiveDocument(null)
        setExtractionDataState(null)
        setRedFlagData(null)

        return false
      } finally {
        if (
          workspaceLoadRef.current?.workspaceId ===
          workspaceId
        ) {
          workspaceLoadRef.current = null
        }
      }
    })()

    workspaceLoadRef.current = {
      workspaceId,
      promise,
    }

    return promise
  }

  // ---------------------------------------------------------
  // PIPELINE RESULTS
  // ---------------------------------------------------------

  function setPipelineResults({
    document,
    extraction,
    redFlags,
  }) {
    setActiveDocument(document)
    setExtractionDataState(extraction)
    setRedFlagData(redFlags)

    if (activeCompany?.id) {
      loadedCompanyIdRef.current =
        String(activeCompany.id)
    }
  }

  // ---------------------------------------------------------
  // CONTEXT
  // ---------------------------------------------------------

  return (
    <WorkspaceContext.Provider
      value={{
        sessions,
        sessionsLoading,

        refreshSessions,
        createSession,
        updateSession,
        deleteSession,
        getSessionDocuments,
        deleteSessionDocument,

        activeWorkspace,
        setActiveWorkspace,

        companies,
        refreshCompanies,
        addCompany,

        activeCompany,
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
    throw new Error(
      'useWorkspace must be used within a WorkspaceProvider'
    )
  }

  return context
}