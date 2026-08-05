import DashboardCard from "./DashboardCard";

function DashboardStats() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

      <DashboardCard
        title="Total Uploads"
        value="10"
        color="bg-blue-600"
      />

      <DashboardCard
        title="Total Sessions"
        value="5"
        color="bg-green-600"
      />

      <DashboardCard
        title="Recent Uploads"
        value="3"
        color="bg-purple-600"
      />

    </div>
  );
}

export default DashboardStats;