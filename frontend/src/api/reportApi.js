// frontend/src/api/reportApi.js
import axiosClient from './axiosClient.js'

// Matches backend/routes/report.py exactly.
// NOTE: report generation is SYNCHRONOUS on the backend -- POST /report/generate
// runs extraction + narrative + PDF build and returns the finished ReportResponse
// in one call. There is no job id / status polling for this agent.

export function generateReport({ workspaceId, companyId, comparisonIds }) {
  const payload = {
    workspace_id: workspaceId,
    company_id: companyId,
  }
  if (comparisonIds && comparisonIds.length > 0) {
    payload.comparison_ids = comparisonIds
  }
  return axiosClient.post('/report/generate', payload)
}

// Preview which completed comparisons would be auto-included if you
// generated a report for this company right now.
export function getAvailableComparisons(companyId, workspaceId) {
  return axiosClient.get(
    `/report/company/${companyId}/available-comparisons`,
    { params: { workspace_id: workspaceId } }
  )
}

export function listReportsForCompany(companyId) {
  return axiosClient.get(`/report/company/${companyId}`)
}

export function getReport(reportId) {
  return axiosClient.get(`/report/${reportId}`)
}

export function downloadReport(reportId) {
  return axiosClient.get(`/report/${reportId}/download`, {
    responseType: 'blob',
  })
}

export function deleteReport(reportId) {
  return axiosClient.delete(`/report/${reportId}`)
}