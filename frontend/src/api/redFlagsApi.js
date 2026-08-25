import axiosClient from './axiosClient.js'

export function runRedFlagAnalysis(documentId) {
  return axiosClient.post('/red-flags/run', { document_id: documentId })
}

export function getRedFlagsForDocument(documentId) {
  return axiosClient.get(`/red-flags/document/${documentId}`)
}