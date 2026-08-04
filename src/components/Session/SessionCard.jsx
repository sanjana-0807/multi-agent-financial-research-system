function SessionCard({session, onDelete}){
    return(
        <div className="border rounded-1g p-4 shadow-md bg-white">
            <h2 className="text-1g font-semibold">{session.name}</h2>
            <p className="text-gray-500 text-sm">
                Created: {session.date}
            </p>
            <div className="mt-4 flex gap-3">
                <button className="bg-blue-600 text-white px-3 py-1 rounded">
                    Open
                </button>
                <button onClick={() => onDelete(session.id)} className="bg-blue-600 text-white px-3 py-1 rounded">
                    Delete
                </button>

            </div>

        </div>
    );
}

export default SessionCard;