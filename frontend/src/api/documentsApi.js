import axiosClient from './axiosClient.js'

export function uploadDocument(file, companyId) {
  const formData = new FormData()
  formData.append('file', file)
  if (companyId) formData.append('company_id', companyId)
  return axiosClient.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getDocument(documentId) {
  return axiosClient.get(`/documents/${documentId}`)
}

export function linkDocumentToCompany(documentId, companyId) {
  return axiosClient.patch(`/documents/${documentId}/link-company`, { company_id: companyId })
}

export function getLatestDocumentForCompany(companyId) {
  return axiosClient.get(`/documents/company/${companyId}/latest`)
}