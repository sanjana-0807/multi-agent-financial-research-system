import Navbar from "../components/Navbar/Navbar";
import Sidebar from "../components/Sidebar/Sidebar";
import DashboardStats from "../components/Dashboard/DashboardStats";

function Dashboard() {
  return (
    <>
      <Navbar />

      <div className="flex">

        <Sidebar />

        <div className="flex-1 p-8 bg-gray-100 min-h-screen">

          <h1 className="text-3xl font-bold mb-8">
            Dashboard
          </h1>

          <DashboardStats />

        </div>

      </div>
    </>
  );
}

export default Dashboard;