import axiosClient from './axiosClient'

export function getExtraction(documentId) {
  return axiosClient.get(`/api/extract/${documentId}`)
}