import { FileText } from 'lucide-react'

function Table({ columns = [], rows = [], emptyText = 'No data records found.' }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-3d-subtle overflow-hidden select-none">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200/80">
              {columns.map((col) => (
                <th 
                  key={col.key} 
                  className={`px-5 py-3.5 text-xs font-bold uppercase tracking-wider text-slate-500 ${col.headerClassName || ''}`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length > 0 ? (
              rows.map((row, i) => (
                <tr 
                  key={row.id || i} 
                  className="hover:bg-blue-50/40 transition-colors duration-150 group"
                >
                  {columns.map((col) => (
                    <td 
                      key={col.key} 
                      className={`px-5 py-4 text-slate-700 font-medium ${col.className || ''}`}
                    >
                      {col.render ? col.render(row[col.key], row) : (row[col.key] !== undefined && row[col.key] !== null ? row[col.key] : '—')}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length || 1} className="px-5 py-12 text-center text-slate-400">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <FileText size={24} className="text-slate-300" />
                    <span className="text-sm font-medium">{emptyText}</span>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Table

