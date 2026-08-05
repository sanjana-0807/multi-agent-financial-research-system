import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="bg-blue-700 text-white p-4 flex justify-between">
      <h1 className="text-xl font-bold">Financial Research System</h1>

      <div className="space-x-4">
        <Link to="/workspace">Workspace</Link>
        <Link to="/upload">Upload</Link>
        <Link to="/sessions">Sessions</Link>
        <Link to="/history">History</Link>
        <Link to="/dashboard">Dashboard</Link>
      </div>
    </nav>
  );
}

export default Navbar;