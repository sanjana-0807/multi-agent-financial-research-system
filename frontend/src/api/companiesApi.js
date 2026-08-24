import axiosClient from './axiosClient.js'

export function createCompany(payload) {
  return axiosClient.post('/companies/', payload)
}

export function listCompanies(workspaceId, skip = 0, limit = 50) {
  return axiosClient.get(`/companies/?workspace_id=${workspaceId}&skip=${skip}&limit=${limit}`)
}

export function getCompany(companyId) {
  return axiosClient.get(`/companies/${companyId}`)
}

export function updateCompany(companyId, payload) {
  return axiosClient.patch(`/companies/${companyId}`, payload)
}

export function deleteCompany(companyId) {
  return axiosClient.delete(`/companies/${companyId}`)
}