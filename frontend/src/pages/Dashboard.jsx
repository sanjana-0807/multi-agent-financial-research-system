import { useState } from 'react'
import './Dashboard.css'
import { dashboardData } from '../data/mockDashboardData.js'
import FinancialCard from '../components/FinancialCard.jsx'
import { DollarSign, TrendingUp, Landmark, ArrowLeftRight, Coins, Scale, Percent } from 'lucide-react'
function Dashboard(){
    const [activeItem, setActiveItem] = useState("Dashboard")
    return(
         <div className="dashboard-layout">
         <div className="sidebar">
            <p
              className={activeItem === "Dashboard" ? "active" : ""}
              onClick={() => setActiveItem("Dashboard")}
            >Dashboard</p>
            <p className={activeItem === "Login" ? "active" : ""} onClick={() => setActiveItem("Login")}>Login</p>
            <p className={activeItem === "Workspace" ? "active" : ""} onClick={() => setActiveItem("Workspace")}>Workspace</p>
            <p className={activeItem === "Upload" ? "active" : ""} onClick={() => setActiveItem("Upload")}>Upload</p>
            <p className={activeItem === "Sessions" ? "active" : ""} onClick={() => setActiveItem("Sessions")}>Sessions</p>
            <p className={activeItem === "Upload History" ? "active" : ""} onClick={() => setActiveItem("Upload History")}>Upload History</p>
            <p className={activeItem === "Metrics" ? "active" : ""} onClick={() => setActiveItem("Metrics")}>Metrics</p>
            <p className={activeItem === "Ratios" ? "active" : ""} onClick={() => setActiveItem("Ratios")}>Ratios</p>
            <p className={activeItem === "Chat" ? "active" : ""} onClick={() => setActiveItem("Chat")}>Chat</p>
            <p className={activeItem === "Comparison" ? "active" : ""} onClick={() => setActiveItem("Comparison")}>Comparison</p>
            <p className={activeItem === "Report" ? "active" : ""} onClick={() => setActiveItem("Report")}>Report</p>
            <p className={activeItem === "Settings" ? "active" : ""} onClick={() => setActiveItem("Settings")}>Settings</p>
         </div>
        <div className="main-content">
          <div className="title-block">
            <h1>Financial Dashboard</h1>
            <h2>{dashboardData.company} - FY {dashboardData.fiscal_year}</h2>
          </div>
        
        <div className="metrics">
        <FinancialCard label="Revenue" value={dashboardData.revenue} icon={DollarSign} unit="USD in millions"/>
        <FinancialCard label="Profit" value={dashboardData.net_profit} icon={TrendingUp} unit="USD in millions"/>
        <FinancialCard label="Assets" value={dashboardData.assets} icon={Landmark} unit="USD in millions"/>
        <FinancialCard label="Liabilities" value={dashboardData.liabilities} icon={TrendingUp} unit="USD in millions"/>
        <FinancialCard label="Cash Flow" value={dashboardData.cash_flow} icon={ArrowLeftRight} unit="USD in millions"/>
        <FinancialCard label="EPS" value={dashboardData.eps} icon={Coins} unit="USD per share"/>
        </div>
        <h3>Ratios</h3>
        <div className="ratios">
        <FinancialCard label="Current Ratio" value={dashboardData.ratios.current_ratio} icon={Scale} unit="ratio"/>
        <FinancialCard label="Debt to Equity" value={dashboardData.ratios.debt_to_equity} icon={Scale} unit="ratio"/>
        <FinancialCard label="Net Profit Margin" value={dashboardData.ratios.net_profit_margin} icon={Percent} unit="%"/>
        </div>
        <div className="charts-row">
        <div className="chart-placeholder">Revenue Chart (Empty Placeholder)</div>
        <div className="chart-placeholder">Profit Chart (Empty Placeholder)</div>
        </div>
                                                      
        </div>
        
        </div>

    )
}
export default Dashboard