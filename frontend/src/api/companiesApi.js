import axiosClient from './axiosClient.js'

// POST /documents/upload - confirmed working, needs auth (already handled
// by axiosClient's interceptor attaching the token automatically)
export function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)

  return axiosClient.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
