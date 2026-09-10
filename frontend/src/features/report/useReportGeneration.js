import { useState, useCallback } from 'react'
import { generateReport, getReportStatus } from '../../api/reportApi.js'
import usePolling from '../../hooks/usePolling.js'
import { POLL_INTERVAL, JOB_STATUS } from '../../utils/constants.js'

// Hook: generate a report → poll status → report ready for preview/download.
function useReportGeneration() {
  const [reportId, setReportId] = useState(null)
  const [status, setStatus] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const isPolling =
    !!reportId &&
    status !== JOB_STATUS.COMPLETED &&
    status !== JOB_STATUS.FAILED

  const pollStatus = useCallback(async () => {
    if (!reportId) return

    try {
      const res = await getReportStatus(reportId)
      setStatus(res.data.status)

      if (res.data.status === JOB_STATUS.COMPLETED) {
        setReport(res.data.report || res.data)
        setLoading(false)
      } else if (res.data.status === JOB_STATUS.FAILED) {
        setError(res.data.error || 'Report generation failed')
        setLoading(false)
      }
    } catch {
      setError('Failed to check report status')
      setLoading(false)
    }
  }, [reportId])

  usePolling(pollStatus, POLL_INTERVAL, isPolling)

  async function generate(documentId, comparisonId = null) {
    setError(null)
    setReport(null)
    setStatus(JOB_STATUS.PENDING)
    setLoading(true)

    try {
      const res = await generateReport(
        documentId,
        comparisonId
      )

      setReportId(res.data.report_id)
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Failed to start report generation'
      )
      setLoading(false)
    }
  }

  function reset() {
    setReportId(null)
    setStatus(null)
    setReport(null)
    setError(null)
    setLoading(false)
  }

  return {
    generate,
    reportId,
    status,
    report,
    loading,
    error,
    reset,
  }
}

export default useReportGeneration