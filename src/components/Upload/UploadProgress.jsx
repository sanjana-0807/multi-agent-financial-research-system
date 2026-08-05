function UploadProgress({ progress }) {
  if (progress === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold mb-2">
        Upload Progress
      </h3>

      <div className="w-full bg-gray-300 rounded-full h-4">
        <div
          className="bg-green-500 h-4 rounded-full transition-all duration-300"
          style={{ width: '${progress}%'}}
        ></div>
      </div>

      <p className="mt-2 text-sm font-medium">
        {progress}% Uploaded
      </p>

      {progress === 100 && (
        <p className="mt-2 text-green-600 font-semibold">
          ✅ Upload Completed Successfully!
        </p>
      )}
    </div>
  );
}

export default UploadProgress;