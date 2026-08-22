import axiosClient from './axiosClient.js'

// POST /documents/upload - confirmed working, needs auth (already handled
// by axiosClient's interceptor attaching the token automatically)
export function uploadDocument(file, companyId = 'C001') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('company_id', companyId)

  return axiosClient.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
