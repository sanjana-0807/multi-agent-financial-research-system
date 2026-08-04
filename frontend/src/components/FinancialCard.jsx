function FinancialCard({label, value, icon: Icon,unit}) {
  return (
    <div className="card">
      <div className="icon-box">
        <Icon/>
      </div>
      <h3>{label}</h3>
      <p className="value">{value ? value : "N/A"}</p>
      <p className="unit">{unit}</p>
    </div>
  )
}
export default FinancialCard