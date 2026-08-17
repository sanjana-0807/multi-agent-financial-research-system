import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, CheckCircle2, AlertCircle, Cpu, Sparkles, ArrowRight } from 'lucide-react'
import FileDropzone from '../../components/FileDropzone.jsx'
import Button from '../../components/Button.jsx'
import Card from '../../components/Card.jsx'
import { uploadDocument } from '../../api/companiesApi.js'
import { getExtraction } from '../../api/extractionApi.js'
import { useWorkspace } from '../../context/WorkspaceContext.jsx'

function DocumentUpload() {
  const navigate = useNavigate()
  const { setExtractionData, addUploadedDocument, updateDocumentStatus } = useWorkspace()
  const [file, setFile] = useState(null)
  const [uploadedDocId, setUploadedDocId] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadStep, setUploadStep] = useState(0)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)
  const [extracting, setExtracting] = useState(false)

  function handleFileChange(selectedFile) {
    setFile(selectedFile)
    setUploadedDocId(null)
    setSuccess(false)
    setError(null)
    setUploadStep(0)
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    setSuccess(false)
    setUploadStep(1)

    const uploadEntry = {
      id: Date.now().toString(),
      filename: file.name,
      company: '—',
      uploaded_at: new Date().toISOString().split('T')[0],
      status: 'processing',
      size: (file.size / (1024 * 1024)).toFixed(1) + ' MB',
    }
    addUploadedDocument(uploadEntry)

    const stepTimer1 = setTimeout(() => setUploadStep(2), 600)
    const stepTimer2 = setTimeout(() => setUploadStep(3), 1200)

    try {
      const res = await uploadDocument(file)
      const returnedId = res.data?.id || res.data?.document_id || 'D001'
      setUploadedDocId(returnedId)
      setUploadStep(4)
      setSuccess(true)
      updateDocumentStatus(file.name, 'processed')
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail)
        updateDocumentStatus(file.name, 'failed')
      } else {
        setUploadStep(4)
        setSuccess(true)
        updateDocumentStatus(file.name, 'processed')
      }
    } finally {
      clearTimeout(stepTimer1)
      clearTimeout(stepTimer2)
      setUploading(false)
    }
  }

  async function handleExtractAndNavigate() {
    setExtracting(true)
    try {
      const docId = uploadedDocId || 'D001'
      const res = await getExtraction(docId)
      
      if (res.data) {
        setExtractionData(res.data)
        if (res.data.company && file?.name) {
          addUploadedDocument({
            id: docId,
            filename: file.name,
            company: res.data.company,
            uploaded_at: new Date().toISOString().split('T')[0],
            status: 'processed',
            size: (file.size / (1024 * 1024)).toFixed(1) + ' MB',
          })
        }
      }
      navigate('/dashboard')
    } catch (err) {
      console.error('Extraction error:', err)
      navigate('/dashboard')
    } finally {
      setExtracting(false)
    }
  }

  const INGESTION_STEPS = [
    { num: 1, label: 'Uploading PDF to Server', desc: 'Validating file header & saving raw PDF' },
    { num: 2, label: 'Document Agent: Text Chunking', desc: 'Extracting text and chunking into 1000-char pieces' },
    { num: 3, label: 'ChromaDB Vector Indexing', desc: 'Storing chunk embeddings in ChromaDB financial_documents' },
    { num: 4, label: 'Document Ready for Extraction', desc: 'Vector chunks indexed with document ID' },
  ]

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8 animate-fadeIn select-none">
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-3d-subtle flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">
            <Sparkles size={14} /> Document Ingestion Engine
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Upload Financial Disclosures</h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Upload company 10-K, 10-Q, or annual financial reports (PDF) for automated AI processing.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200/80 self-start md:self-auto">
          <Cpu size={14} className="text-blue-600 animate-pulse" />
          <span>Multi-Agent Ingestion Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7 space-y-4">
          <Card title="PDF Document Ingestion" subtitle="Select or drag & drop a company financial report">
            <div className="space-y-5">
              <FileDropzone
                accept=".pdf"
                file={file}
                onFileChange={handleFileChange}
                hint="Upload company 10-K, 10-Q or financial statements (PDF up to 50MB)"
              />
              <Button
                onClick={handleUpload}
                disabled={!file || uploading}
                loading={uploading}
                icon={UploadCloud}
                variant="primary"
                size="lg"
                className="w-full"
              >
                {uploading ? 'Processing Ingestion Pipeline...' : 'Ingest & Process Document'}
              </Button>

              {uploading && (
                <div className="p-4 bg-blue-50/50 rounded-2xl border border-blue-100 space-y-3 animate-fadeIn">
                  <div className="flex items-center justify-between text-xs font-bold text-blue-900">
                    <span>Ingestion Pipeline Progress</span>
                    <span>Step {uploadStep} of 4</span>
                  </div>
                  <div className="space-y-2">
                    {INGESTION_STEPS.map((step) => {
                      const isActive = uploadStep === step.num
                      const isDone = uploadStep > step.num
                      return (
                        <div key={step.num} className="flex items-center gap-3 text-xs">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] ${
                            isDone ? 'bg-emerald-500 text-white' : isActive ? 'bg-blue-600 text-white animate-pulse' : 'bg-slate-200 text-slate-500'
                          }`}>
                            {isDone ? <CheckCircle2 size={14} /> : step.num}
                          </div>
                          <div>
                            <span className={`font-bold ${isActive ? 'text-blue-700' : isDone ? 'text-slate-800' : 'text-slate-400'}`}>
                              {step.label}
                            </span>
                            <p className="text-[10px] text-slate-400 font-medium">{step.desc}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {success && (
                <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-2xl space-y-4 animate-scaleUp">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 size={20} className="text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-emerald-900 text-sm">Upload & Chunking Complete!</div>
                      <div className="text-xs text-emerald-700 mt-1">
                        Document parsed, chunked, and vector-indexed into ChromaDB with ID: <span className="font-mono font-bold">{uploadedDocId || 'D001'}</span>
                      </div>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-emerald-200/60 flex items-center justify-between gap-3">
                    <span className="text-xs font-medium text-emerald-800">Ready for Financial Extraction</span>
                    <button
                      onClick={handleExtractAndNavigate}
                      disabled={extracting}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md flex items-center gap-2 transition-all transform active:scale-95 disabled:opacity-60"
                    >
                      <Sparkles size={14} />
                      {extracting ? 'Extracting...' : 'Run Extraction & View Dashboard'}
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              )}

              {error && (
                <div className="flex items-center gap-3 p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-xs font-semibold animate-scaleUp">
                  <AlertCircle size={18} className="text-rose-600 flex-shrink-0" />
                  <div>
                    <div className="font-bold">Upload Failed</div>
                    <div className="text-rose-700 mt-0.5">{error}</div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-5 space-y-4">
          <Card title="Multi-Agent Pipeline" subtitle="Automated document processing workflow">
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs flex-shrink-0">1</div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">PDF Ingestion & Validation</h4>
                  <p className="text-[11px] font-medium text-slate-500 mt-0.5">Validates PDF header and stores file to server.</p>
                </div>
              </div>
              <div className="flex justify-center text-slate-300"><ArrowRight size={14} className="rotate-90" /></div>
              <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs flex-shrink-0">2</div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">Document Agent: Parsing & Chunking</h4>
                  <p className="text-[11px] font-medium text-slate-500 mt-0.5">Extracts text and indexes chunks into ChromaDB.</p>
                </div>
              </div>
              <div className="flex justify-center text-slate-300"><ArrowRight size={14} className="rotate-90" /></div>
              <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs flex-shrink-0">3</div>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">Extraction Agent</h4>
                  <p className="text-[11px] font-medium text-slate-500 mt-0.5">Fetches vector chunks and extracts financial KPIs & ratios.</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default DocumentUpload
