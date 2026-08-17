import axiosClient from './axiosClient.js'

// Matches backend/routes/research.py
// POST /research/extract - extraction (already in extractionApi.js)
// POST /research/redflag - red flag analysis (confirmed working endpoint)

export function submitResearchPrompt(documentId, prompt) {
  return axiosClient.post('/research/prompt', { document_id: documentId, prompt })
}

export function getResearchStatus(jobId) {
  return axiosClient.get(`/research/status/${jobId}`)
}

export function getResearchResults(jobId) {
  return axiosClient.get(`/research/results/${jobId}`)
}

export function getRedFlagAnalysis(documentId) {
  return axiosClient.post('/research/redflag', { document_id: documentId })
}
