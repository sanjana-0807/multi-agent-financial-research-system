import { useRef } from "react";

function UploadBox({ onFileSelect }) {
  const inputRef = useRef();

  const handleChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="bg-white border-2 border-dashed border-gray-400 rounded-lg p-8 text-center">

      <h2 className="text-xl font-semibold mb-4">
        Upload Financial Report
      </h2>

      <p className="text-gray-500 mb-4">
        Select a PDF document to upload.
      </p>

      <input
        type="file"
        accept=".pdf"
        ref={inputRef}
        onChange={handleChange}
        hidden
      />

      <button
        onClick={() => inputRef.current.click()}
        className="bg-blue-600 text-white px-5 py-2 rounded"
      >
        Choose PDF
      </button>

    </div>
  );
}

export default UploadBox;