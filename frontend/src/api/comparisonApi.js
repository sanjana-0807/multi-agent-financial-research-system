import axiosClient from './axiosClient.js'

export function runComparison(workspaceId, companyIds) {
  return axiosClient.post('/comparison/run', { workspace_id: workspaceId, company_ids: companyIds })
}

export function getComparison(comparisonId) {
  return axiosClient.get(`/comparison/${comparisonId}`)
}

// workspaceId is required in practice -- omitting it returns every
// comparison in the system across every workspace, and a fixed
// skip/limit page can then permanently miss this workspace's own
// recent comparisons once the global collection grows past that page.
export function listComparisons(workspaceId, skip = 0, limit = 50) {
  const params = new URLSearchParams({ skip, limit })
  if (workspaceId) params.set('workspace_id', workspaceId)
  return axiosClient.get(`/comparison/?${params.toString()}`)
}