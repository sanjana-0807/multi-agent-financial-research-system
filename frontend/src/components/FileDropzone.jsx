import { useState } from 'react'
import { UploadCloud, FileText, X, CheckCircle2 } from 'lucide-react'

function FileDropzone({ accept = '.pdf', file, onFileChange, hint }) {
  const [isDragOver, setIsDragOver] = useState(false)

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave() {
    setIsDragOver(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileChange?.(e.dataTransfer.files[0])
    }
  }

  return (
    <div className="w-full select-none">
      {file ? (
        /* Selected File Card View */
        <div className="relative flex items-center justify-between p-4 bg-blue-50/60 border border-blue-200/80 rounded-2xl shadow-sm transition-all animate-scaleUp">
          <div className="flex items-center gap-3.5 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs flex-shrink-0">
              <FileText size={20} />
            </div>
            <div className="truncate">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-900 truncate">{file.name}</span>
                <CheckCircle2 size={14} className="text-emerald-500 flex-shrink-0" />
              </div>
              <p className="text-xs font-medium text-slate-500">
                {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for ingestion
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onFileChange?.(null)}
            className="text-slate-400 hover:text-rose-600 p-1.5 rounded-xl hover:bg-white transition-colors flex-shrink-0"
            title="Remove selected file"
          >
            <X size={18} />
          </button>
        </div>
      ) : (
        /* Drag and Drop Zone */
        <label
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-8 cursor-pointer transition-all duration-300 ${
            isDragOver 
              ? 'border-blue-600 bg-blue-50/60 scale-[1.01] shadow-md' 
              : 'border-slate-300/80 hover:border-blue-400 bg-slate-50/50 hover:bg-blue-50/30 shadow-3d-subtle'
          }`}
        >
          <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 flex items-center justify-center text-blue-600 shadow-sm mb-3 group-hover:scale-110 transition-transform">
            <UploadCloud size={28} className="animate-bounce-slow" />
          </div>

          <span className="text-sm font-bold text-slate-800 tracking-tight">
            Click to upload or drag & drop file
          </span>
          <p className="text-xs font-medium text-slate-400 mt-1">
            {hint || 'Supported format: Financial Report PDF (up to 50MB)'}
          </p>

          <input
            type="file"
            accept={accept}
            onChange={(e) => onFileChange?.(e.target.files[0])}
            className="hidden"
          />
        </label>
      )}
    </div>
  )
}

export default FileDropzone

