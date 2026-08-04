function FeatureCard({ title, description, buttonText, onClick }) {
  return (
    <div className="bg-white shadow-lg rounded-lg p-6">
      <h2 className="text-xl font-bold mb-2">{title}</h2>

      <p className="text-gray-600 mb-4">
        {description}
      </p>

      <button
        onClick={onClick}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        {buttonText}
      </button>
    </div>
  );
}

export default FeatureCard;