function Input({ label, error, ...props }) {
  return (
    <div>
      {label && (
        <label className="block text-sm text-gray-600 mb-1">{label}</label>
      )}
      <input
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        {...props}
      />
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  )
}

export default Input
