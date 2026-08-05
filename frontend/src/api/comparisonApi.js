import axiosClient from './axiosClient.js'

// Matches backend/routes/comparison.py

export function compareCompanies(documentIds) {
  return axiosClient.post('/comparison/compare', { document_ids: documentIds })
}

export function getComparisonResult(comparisonId) {
  return axiosClient.get(`/comparison/result/${comparisonId}`)
}
