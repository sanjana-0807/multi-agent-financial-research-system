function FilePreview({ file, removeFile }) {
  if (!file) return null;

  return (
    <div className="bg-white shadow rounded-lg p-4 mt-6">

      <h3 className="font-bold">Selected File</h3>

      <p>Name: {file.name}</p>

      <p>
        Size: {(file.size / 1024).toFixed(2)} KB
      </p>

      <button
        onClick={removeFile}
        className="mt-3 bg-red-500 text-white px-4 py-2 rounded"
      >
        Remove
      </button>

    </div>
  );
}

export default FilePreview;