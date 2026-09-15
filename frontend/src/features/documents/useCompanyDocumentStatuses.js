import { useState, useEffect, useRef } from 'react'
import { getLatestDocumentForCompany } from '../../api/documentsApi.js'

// Fetches the latest document for EVERY company passed in, so UI that
// lists all companies in a workspace (the "Companies in This Session"
// pills, the Document Agent list) can show an accurate Ready/No document
// status for companies other than the one currently active in
// WorkspaceContext.
//
// WorkspaceContext only ever loads document data for the single active
// company. Relying on that alone for a multi-company list means every
// non-active company falls back to "no document", even when a document
// exists for it in the backend.
function useCompanyDocumentStatuses(companies) {
  const [statusByCompany, setStatusByCompany] = useState({})
  const [loading, setLoading] = useState(false)

  // Tracks which company ids we've already fetched (or are fetching),
  // so re-renders don't refire requests for companies we already have
  // an answer for.
  const fetchedIdsRef = useRef(new Set())

  // IMPORTANT: depend on a stable, order-independent key built from the
  // company ids rather than the `companies` array reference itself.
  // WorkspaceContext's workspace-loading flow produces several fresh
  // array references for the same underlying companies while data is
  // still loading (setCompanies is called more than once). If the effect
  // depended on the array reference, it would re-run and its cleanup
  // would set `cancelled = true` on the still in-flight fetch from the
  // previous run — so when that fetch resolved, its result was silently
  // discarded (the callback bailed out on `cancelled`), while the
  // company id had already been marked "fetched" and was never retried.
  // The net effect: statuses randomly never populated, including for
  // the active company that clearly does have a document.
  const idsKey = (companies || []).map((c) => String(c.id)).sort().join(',')

  useEffect(() => {
    if (!companies || companies.length === 0) {
      setStatusByCompany({})
      fetchedIdsRef.current = new Set()
      return
    }

    const idsInScope = new Set(companies.map((c) => String(c.id)))

    // Drop cached statuses for companies no longer in scope
    // (e.g. switched workspace).
    setStatusByCompany((prev) => {
      const next = {}
      for (const key of Object.keys(prev)) {
        if (idsInScope.has(key)) next[key] = prev[key]
      }
      return next
    })
    for (const id of fetchedIdsRef.current) {
      if (!idsInScope.has(id)) fetchedIdsRef.current.delete(id)
    }

    const companiesToFetch = companies.filter(
      (c) => !fetchedIdsRef.current.has(String(c.id))
    )

    if (companiesToFetch.length === 0) return

    setLoading(true)
    companiesToFetch.forEach((c) => fetchedIdsRef.current.add(String(c.id)))

    // No `cancelled` guard here on purpose: applying a result after this
    // effect has re-run is always safe (it just writes the same company's
    // correct status), whereas discarding it is what caused the bug.
    Promise.allSettled(
      companiesToFetch.map((c) => getLatestDocumentForCompany(c.id))
    ).then((results) => {
      setStatusByCompany((prev) => {
        const next = { ...prev }
        results.forEach((result, idx) => {
          const companyId = String(companiesToFetch[idx].id)
          next[companyId] =
            result.status === 'fulfilled' ? result.value.data : null
        })
        return next
      })
      setLoading(false)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idsKey])

  return { statusByCompany, loading }
}

export default useCompanyDocumentStatuses