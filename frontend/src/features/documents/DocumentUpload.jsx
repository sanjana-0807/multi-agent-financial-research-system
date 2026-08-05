import { useState } from 'react'
import { Upload as UploadIcon, CheckCircle, XCircle } from 'lucide-react'
import { uploadDocument } from '../../api/companiesApi.js'

function DocumentUpload() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  function handleFileChange(e) {
    setFile(e.target.files[0])
    setSuccess(false)
    setError(null)
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    setSuccess(false)

    try {
      await uploadDocument(file)
      setSuccess(true)
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed - try again')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Upload Document</h1>
      <p className="text-gray-500 mb-6">Upload a company financial report (PDF) to begin analysis.</p>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 max-w-lg">
        <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg py-10 cursor-pointer hover:border-blue-400 transition-colors">
          <UploadIcon size={28} className="text-gray-400 mb-2" />
          <span className="text-sm text-gray-500">
            {file ? file.name : 'Click to choose a PDF file'}
          </span>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full mt-4 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>

        {success && (
          <div className="flex items-center gap-2 mt-4 text-green-600 text-sm">
            <CheckCircle size={16} />
            Document uploaded successfully
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 mt-4 text-red-500 text-sm">
            <XCircle size={16} />
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default DocumentUpload
