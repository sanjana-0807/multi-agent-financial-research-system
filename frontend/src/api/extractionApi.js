import axiosClient from './axiosClient'

// Updated to match team's real endpoint: POST /research/extract
// (was previously GET /api/extract/{document_id} which was our own route)
export function getExtraction(documentId) {
  return axiosClient.post('/research/extract', { document_id: documentId })
}
