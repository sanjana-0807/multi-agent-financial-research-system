import axiosClient from './axiosClient.js'

export function listWorkspaces() {
  return axiosClient.get('/workspaces/')
}

export function createWorkspace(payload) {
  return axiosClient.post('/workspaces/', payload)
}

export function getWorkspace(id) {
  return axiosClient.get(`/workspaces/${id}`)
}

export function updateWorkspace(id, payload) {
  return axiosClient.patch(`/workspaces/${id}`, payload)
}

export function getWorkspaceDocuments(id) {
  return axiosClient.get(`/workspaces/${id}/documents`)
}

export function deleteWorkspace(id) {
  return axiosClient.delete(`/workspaces/${id}`)
}