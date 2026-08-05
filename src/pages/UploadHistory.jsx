import { useEffect, useState } from "react";
import Navbar from "../components/Navbar/Navbar";
import Sidebar from "../components/Sidebar/Sidebar";
import HistoryTable from "../components/History/HistoryTable";

function UploadHistory() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const data =
      JSON.parse(localStorage.getItem("uploadHistory")) || [];
    setHistory(data);
  }, []);

  const deleteFile = (id) => {
    const updatedHistory = history.filter((item) => item.id !== id);

    setHistory(updatedHistory);

    localStorage.setItem(
      "uploadHistory",
      JSON.stringify(updatedHistory)
    );
  };

  return (
    <>
      <Navbar />

      <div className="flex">
        <Sidebar />

        <div className="flex-1 p-8 bg-gray-100 min-h-screen">
          <h1 className="text-3xl font-bold mb-6">
            Upload History
          </h1>

          <HistoryTable
            history={history}
            deleteFile={deleteFile}
          />
        </div>
      </div>
    </>
  );
}

export default UploadHistory;