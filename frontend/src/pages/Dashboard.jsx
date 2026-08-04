import './Dashboard.css'
import FinancialCard from '../components/FinancialCard.jsx'
import { DollarSign, TrendingUp, Landmark, ArrowLeftRight, Coins, Scale, Percent } from 'lucide-react'
function Dashboard(){
    return(
        <>
        <h1>Financial Dashboard</h1>
        <h2>Tesla - FY 2025</h2>
        <div className="metrics">
        <FinancialCard label="Revenue" value={879891} icon={DollarSign}/>
        <FinancialCard label="Profit" value={74982} icon={TrendingUp}/>
        <FinancialCard label="Assets" value={247489282} icon={Landmark}/>
        <FinancialCard label="Liabilities" value={628742} icon={TrendingUp}/>
        <FinancialCard label="Cash Flow" value={82782732} icon={ArrowLeftRight}/>
        <FinancialCard label="EPS" value={847289} icon={Coins}/>
        </div>
        <h3>Ratios</h3>
        <div className="ratios">
        <FinancialCard label="Current Ratio" value={1.8} icon={Scale}/>
        <FinancialCard label="Debt to Equity" value={0.38} icon={Scale}/>
        <FinancialCard label="Net Profit Margin" value={18.9} icon={Percent}/>
        </div>
        <div className="charts-row">
        <div className="chart-placeholder">Revenue Chart (Empty Placeholder)</div>
        <div className="chart-placeholder">Profit Chart (Empty Placeholder)</div>
        </div>
                                                      
        
        </>
    )
}
export default Dashboard