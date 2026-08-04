function FinancialCard({ label, value, icon: Icon }) {
    return (
        <div className="card">
            <h3>{label}</h3>
            <div className="value-row">
                <Icon />
                <p>{value}</p>
            </div>
        </div>
    )
}
export default FinancialCard