import { Upload } from 'lucide-react'

function FileDropzone({ accept = '.pdf', file, onFileChange, hint }) {
  return (
    <label className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg py-10 cursor-pointer hover:border-blue-400 transition-colors">
      <Upload size={28} className="text-gray-400 mb-2" />
      <span className="text-sm text-gray-500">
        {file ? file.name : hint || 'Click to choose a file'}
      </span>
      <input
        type="file"
        accept={accept}
        onChange={(e) => onFileChange(e.target.files[0])}
        className="hidden"
      />
    </label>
  )
}

export default FileDropzone
