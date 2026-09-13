// frontend/src/features/report/useReportGeneration.js
import { useState, useCallback } from 'react'
import {
  generateReport,
  getAvailableComparisons,
  listReportsForCompany,
  deleteReport as apiDeleteReport,
} from '../../api/reportApi.js'

// Hook: load available comparisons for a company -> generate report
// (synchronous on the backend) -> report ready for preview/download.
// Also tracks this company's report history so past reports can be
// reopened without regenerating.
function useReportGeneration() {
  const [report, setReport] = useState(null)
  const [reports, setReports] = useState([])
  const [availableComparisons, setAvailableComparisons] = useState([])

  const [loading, setLoading] = useState(false)
  const [loadingComparisons, setLoadingComparisons] = useState(false)
  const [loadingReports, setLoadingReports] = useState(false)
  const [error, setError] = useState(null)

  const loadAvailableComparisons = useCallback(async (companyId, workspaceId) => {
    if (!companyId || !workspaceId) {
      setAvailableComparisons([])
      return
    }
    setLoadingComparisons(true)
    try {
      const res = await getAvailableComparisons(companyId, workspaceId)
      setAvailableComparisons(res.data)
    } catch {
      setAvailableComparisons([])
    } finally {
      setLoadingComparisons(false)
    }
  }, [])

  const loadReports = useCallback(async (companyId) => {
    if (!companyId) {
      setReports([])
      return
    }
    setLoadingReports(true)
    try {
      const res = await listReportsForCompany(companyId)
      setReports(res.data)
    } catch {
      setReports([])
    } finally {
      setLoadingReports(false)
    }
  }, [])

  async function generate(workspaceId, companyId, comparisonIds) {
    if (!workspaceId || !companyId) return null
    setError(null)
    setLoading(true)
    try {
      const res = await generateReport({ workspaceId, companyId, comparisonIds })
      setReport(res.data)
      await loadReports(companyId)
      return res.data
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate report')
      return null
    } finally {
      setLoading(false)
    }
  }

  async function removeReport(reportId, companyId) {
    try {
      await apiDeleteReport(reportId)
      setReport((current) => (current?.id === reportId ? null : current))
      await loadReports(companyId)
    } catch {
      setError('Failed to delete report')
    }
  }

  function reset() {
    setReport(null)
    setError(null)
  }

  return {
    report,
    setReport,
    reports,
    availableComparisons,
    loading,
    loadingComparisons,
    loadingReports,
    error,
    generate,
    loadAvailableComparisons,
    loadReports,
    removeReport,
    reset,
  }
}

export default useReportGeneration