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

export function deleteWorkspace(id) {
  return axiosClient.delete(`/workspaces/${id}`)
}