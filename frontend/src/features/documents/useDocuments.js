import { useState, useEffect } from 'react'
import axiosClient from '../../api/axiosClient.js'
import { uploadDocument } from '../../api/companiesApi.js'

// Hook for fetching document list and uploading new documents.
function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploading, setUploading] = useState(false)

  async function fetchDocuments() {
    setLoading(true)
    setError(null)
    try {
      const res = await axiosClient.get('/documents')
      setDocuments(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load documents')
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  async function upload(file) {
    setUploading(true)
    try {
      const res = await uploadDocument(file)
      // refresh list after upload
      await fetchDocuments()
      return res.data
    } catch (err) {
      throw err
    } finally {
      setUploading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  return { documents, loading, error, uploading, upload, refresh: fetchDocuments }
}

export default useDocuments
