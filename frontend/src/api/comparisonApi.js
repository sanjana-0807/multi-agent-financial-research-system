import axiosClient from './axiosClient.js'

export function runComparison(workspaceId, companyIds) {
  return axiosClient.post('/comparison/run', { workspace_id: workspaceId, company_ids: companyIds })
}

export function getComparison(comparisonId) {
  return axiosClient.get(`/comparison/${comparisonId}`)
}

export function listComparisons(skip = 0, limit = 50) {
  return axiosClient.get(`/comparison/?skip=${skip}&limit=${limit}`)
}