import { useState, useEffect } from 'react'
import axiosClient from '../../api/axiosClient.js'

// Hook for fetching and managing workspace/session list.
// Returns the list, loading state, error, and a refresh function.
function useWorkspaces() {
  const [workspaces, setWorkspaces] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function fetchWorkspaces() {
    setLoading(true)
    setError(null)
    try {
      const res = await axiosClient.get('/workspaces')
      setWorkspaces(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load sessions')
      setWorkspaces([])
    } finally {
      setLoading(false)
    }
  }

  async function createWorkspace(data) {
    const res = await axiosClient.post('/workspaces', data)
    // refresh the list after creating
    await fetchWorkspaces()
    return res.data
  }

  useEffect(() => {
    fetchWorkspaces()
  }, [])

  return { workspaces, loading, error, refresh: fetchWorkspaces, createWorkspace }
}

export default useWorkspaces
