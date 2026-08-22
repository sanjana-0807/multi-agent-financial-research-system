function Loader({ text = 'Loading...' }) {
  return (
    <div className="flex items-center justify-center py-10">
      <p className="text-gray-400 text-sm">{text}</p>
    </div>
  )
}

export default Loader
