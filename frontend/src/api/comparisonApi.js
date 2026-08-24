import axiosClient from './axiosClient.js'

// Matches backend/routes/comparison.py

export function runComparison(companyIds) {
  return axiosClient.post('/comparison/run', { company_ids: companyIds })
}

export function getComparison(comparisonId) {
  return axiosClient.get(`/comparison/${comparisonId}`)
}

export function listComparisons(skip = 0, limit = 50) {
  return axiosClient.get(`/comparison/?skip=${skip}&limit=${limit}`)  // was missing trailing slash
}

// Backward compatibility alias
export const compareCompanies = runComparison
export const getComparisonResult = getComparison
