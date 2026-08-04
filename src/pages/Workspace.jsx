import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar/Navbar";
import Sidebar from "../components/Sidebar/Sidebar";
import FeatureCard from "../components/Workspace/FeatureCard";
function Workspace() {
  const navigate = useNavigate();

  return (
    <>
    <Navbar/>
    <div className="flex">
      <Sidebar/>
    <div className="min-h-screen bg-gray-100 p-8">

      <h1 className="text-3xl font-bold mb-6">
        Financial Research Workspace
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              title="Create Research Sessions"
              description="Create and manage research sessions."
              buttonText="Open"
              onClick={() => navigate("/sessions")}
            />

            <FeatureCard
              title="Upload Financial Report"
              description="Upload PDF reports for analysis."
              buttonText="Upload"
              onClick={() => navigate("/upload")}
            />

            <FeatureCard
              title="Upload History"
              description="View previously uploaded reports."
              buttonText="View history"
              onClick={() => navigate("/history")}
            />

        {/* Create Session Card */}
        {/*<div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold">
            Create Research Session
          </h2>

          <p className="text-gray-500 mt-2">
            Start a new financial research session.
          </p>

          <button
            onClick={() => navigate("/sessions")}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded"
          >
            Create Session
          </button>
        </div>*/}

        {/* Upload PDF */}
        {/*<div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold">
            Upload Financial Report
          </h2>

          <p className="text-gray-500 mt-2">
            Upload Annual Report or 10-K PDF.
          </p>

          <button
            onClick={() => navigate("/upload")}
            className="mt-4 bg-green-600 text-white px-4 py-2 rounded"
          >
            Upload PDF
          </button>
        </div>*/}

        {/* Upload History */}
        {/*<div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold">
            Upload History
          </h2>

          <p className="text-gray-500 mt-2">
            View uploaded documents.
          </p>

          <button
            onClick={() => navigate("/history")}
            className="mt-4 bg-purple-600 text-white px-4 py-2 rounded"
          >
            View History
          </button>
        </div>*/}
    </div>

      </div>

    </div>
    </>
  );
}

export default Workspace;