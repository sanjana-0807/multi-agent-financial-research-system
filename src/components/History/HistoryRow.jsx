function HistoryRow({ item, deleteFile }) {
  return (
    <tr className="border-b">
      <td className="w-1/4 p-4 text-center">{item.name}</td>
      <td className="w-1/4 p-4 text-center">{item.date}</td>
      <td className="w-1/4 p-4 text-center">{item.status}</td>
      <td className="w-1/4 p-4 text-center">
        <button
          onClick={() => deleteFile(item.id)}
          className="bg-red-500 text-white px-3 py-1 rounded"
        >
          Delete
        </button>
      </td>
    </tr>
  );
}

export default HistoryRow;