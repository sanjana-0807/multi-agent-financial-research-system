import { useState } from "react";
import Navbar from "../components/Navbar/Navbar";
import Sidebar from "../components/Sidebar/Sidebar";
import UploadBox from "../components/Upload/UploadBox";
import FilePreview from "../components/Upload/FilePreview";
import UploadProgress from "../components/Upload/UploadProgress";

function Upload() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);

  const removeFile = () => {
    setFile(null);
    setProgress(0);
  };

  const uploadFile = () => {
    if (!file) {
      alert("Please select a PDF file.");
      return;
    }

    let value = 0;

    const timer = setInterval(() => {
      value += 10;
      setProgress(value);

      if (value >= 100) {
        clearInterval(timer);

        const history =
          JSON.parse(localStorage.getItem("uploadHistory")) || [];

        history.push({
          id: Date.now(),
          name: file.name,
          date: new Date().toLocaleDateString(),
          status: "Uploaded",
        });

        localStorage.setItem(
          "uploadHistory",
          JSON.stringify(history)
        );

        alert("Upload Successful!");
      }
    }, 300);
  };

  return (
    <>
      <Navbar />

      <div className="flex">
        <Sidebar />

        <div className="flex-1 p-8 bg-gray-100 min-h-screen">

          <h1 className="text-3xl font-bold mb-6">
            Upload Financial Report
          </h1>

          <UploadBox onFileSelect={setFile} />

          <FilePreview
            file={file}
            removeFile={removeFile}
          />

          <UploadProgress progress={progress} />

          {file && (
            <button
              onClick={uploadFile}
              className="mt-6 bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
            >
              Upload PDF
            </button>
          )}

        </div>
      </div>
    </>
  );
}

export default Upload;