import { useState, useCallback } from 'react'
import { submitResearchPrompt, getResearchStatus, getResearchResults } from '../../api/researchApi.js'
import usePolling from '../../hooks/usePolling.js'
import { POLL_INTERVAL, JOB_STATUS } from '../../utils/constants.js'

// Hook: submit a research prompt → poll job status → get consolidated result.
// Usage:
//   const { submit, status, result, error, loading } = useResearchJob()
//   await submit(documentId, prompt)
//   // status updates automatically via polling until completed/failed
function useResearchJob() {
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const isPolling = !!jobId && status !== JOB_STATUS.COMPLETED && status !== JOB_STATUS.FAILED

  const pollStatus = useCallback(async () => {
    if (!jobId) return
    try {
      const res = await getResearchStatus(jobId)
      setStatus(res.data.status)

      if (res.data.status === JOB_STATUS.COMPLETED) {
        const resultRes = await getResearchResults(jobId)
        setResult(resultRes.data)
        setLoading(false)
      } else if (res.data.status === JOB_STATUS.FAILED) {
        setError(res.data.error || 'Research job failed')
        setLoading(false)
      }
    } catch (err) {
      setError('Failed to check job status')
      setLoading(false)
    }
  }, [jobId])

  usePolling(pollStatus, POLL_INTERVAL, isPolling)

  async function submit(documentId, prompt) {
    setError(null)
    setResult(null)
    setStatus(JOB_STATUS.PENDING)
    setLoading(true)
    try {
      const res = await submitResearchPrompt(documentId, prompt)
      setJobId(res.data.job_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit research prompt')
      setLoading(false)
    }
  }

  function reset() {
    setJobId(null)
    setStatus(null)
    setResult(null)
    setError(null)
    setLoading(false)
  }

  return { submit, status, result, error, loading, reset }
}

export default useResearchJob
