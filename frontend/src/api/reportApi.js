import axiosClient from './axiosClient.js'

// Matches backend report generation/export/download

export function generateReport(documentId) {
  return axiosClient.post('/report/generate', null, {
    params: { document_id: documentId }
  })
}

export function getReportStatus(reportId) {
  return axiosClient.get(`/report/status/${reportId}`)
}

export function downloadReport(reportId) {
  return axiosClient.get(`/report/download/${reportId}`, {
    responseType: 'blob'
  })
}