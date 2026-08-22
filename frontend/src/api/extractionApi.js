import axiosClient from './axiosClient.js'

export function getExtraction(documentId) {
  return axiosClient.get(`/extraction/${documentId}`)
}

export function runExtraction(documentId) {
  return axiosClient.post('/extraction/run', { document_id: documentId })
}