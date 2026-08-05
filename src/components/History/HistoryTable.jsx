import HistoryRow from "./HistoryRow";

function HistoryTable({ history, deleteFile }) {
  return (
    <div className="flex justify-center mt-10">
      <table className="w-4/5 table-fixed border border-gray-300 bg-white shadow-lg rounded-lg">
        <thead>
          <tr className="bg-gray-200">
            <th className="w-1/4 p-4 text-center">File Name</th>
            <th className="w-1/4 p-4 text-center">Upload Date</th>
            <th className="w-1/4 p-4 text-center">Status</th>
            <th className="w-1/4 p-4 text-center">Action</th>
          </tr>
        </thead>

        <tbody>
          {history.length === 0 ? (
            <tr>
              <td colSpan="4" className="text-center py-8">
                No uploaded files found.
              </td>
            </tr>
          ) : (
            history.map((item) => (
              <HistoryRow
                key={item.id}
                item={item}
                deleteFile={deleteFile}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default HistoryTable;