import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="w-64 h-screen bg-gray-900 text-white p-5">

      <h2 className="text-2xl font-bold mb-8">
        Research System
      </h2>

      <ul className="space-y-4">

        <li>
          <Link
            to="/workspace"
            className="block p-2 rounded hover:bg-gray-700"
          >
            🏠 Workspace
          </Link>
        </li>

        <li>
          <Link
            to="/sessions"
            className="block p-2 rounded hover:bg-gray-700"
          >
            📁 Sessions
          </Link>
        </li>

        <li>
          <Link
            to="/upload"
            className="block p-2 rounded hover:bg-gray-700"
          >
            📤 Upload Document
          </Link>
        </li>

        <li>
          <Link
            to="/history"
            className="block p-2 rounded hover:bg-gray-700"
          >
            📜 Upload History
          </Link>
        </li>

        <li>
           <Link
             to="/dashboard"
             className="block p-2 rounded hover:bg-gray-700"
           >
            📊 Dashboard
           </Link>
        </li>

        <li>
          <Link
            to="/"
            className="block p-2 rounded hover:bg-red-600"
          >
            🚪 Logout
          </Link>
        </li>

      </ul>

    </div>
  );
}

export default Sidebar;