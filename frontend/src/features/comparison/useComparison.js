import { useState } from 'react'
import { compareCompanies, getComparisonResult } from '../../api/comparisonApi.js'

// Hook for managing comparison workflow:
// select documents → submit comparison → get results.
function useComparison() {
  const [selectedIds, setSelectedIds] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function toggleDocument(documentId) {
    setSelectedIds((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId]
    )
  }

  async function runComparison() {
    if (selectedIds.length < 2) return
    setLoading(true)
    setError(null)
    try {
      const res = await compareCompanies(selectedIds)
      // If the backend returns results directly
      if (res.data.companies || res.data.results) {
        setResult(res.data)
      } else if (res.data.comparison_id) {
        // If async — fetch the result
        const resultRes = await getComparisonResult(res.data.comparison_id)
        setResult(resultRes.data)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setSelectedIds([])
    setResult(null)
    setError(null)
  }

  return { selectedIds, toggleDocument, runComparison, result, loading, error, reset }
}

export default useComparison
