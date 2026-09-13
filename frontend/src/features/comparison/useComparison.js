import { useState } from 'react'
import {
  runComparison as runComparisonApi,
  getComparison,
} from '../../api/comparisonApi.js'

function useComparison() {
  const [selectedIds, setSelectedIds] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [error, setError] = useState(null)

  function toggleDocument(documentId) {
    setSelectedIds((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : prev.length < 2
          ? [...prev, documentId]
          : [prev[1], documentId]
    )
  }

  async function runComparison(workspaceId) {
    if (!workspaceId || selectedIds.length !== 2) return null

    setLoading(true)
    setError(null)

    try {
      const res = await runComparisonApi(workspaceId, selectedIds)
      setResult(res.data)
      return res.data
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Comparison failed — make sure both companies have a processed document.'
      )
      return null
    } finally {
      setLoading(false)
    }
  }

  async function loadComparison(comparisonId) {
    if (!comparisonId) return null

    setLoadingHistory(true)
    setError(null)

    try {
      const res = await getComparison(comparisonId)
      setResult(res.data)

      // A saved comparison determines the companies currently displayed.
      setSelectedIds(res.data.company_ids || [])

      return res.data
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to load the saved comparison.'
      )
      return null
    } finally {
      setLoadingHistory(false)
    }
  }

  function reset() {
    setSelectedIds([])
    setResult(null)
    setError(null)
  }

  return {
    selectedIds,
    toggleDocument,
    runComparison,
    loadComparison,
    result,
    loading,
    loadingHistory,
    error,
    reset,
  }
}

export default useComparison