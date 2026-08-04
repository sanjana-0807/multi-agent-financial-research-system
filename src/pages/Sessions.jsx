import { useState, useEffect } from "react";
import SessionCard from "../components/Session/SessionCard";
import Navbar from "../components/Navbar/Navbar";
import Sidebar from "../components/Sidebar/Sidebar";
function Sessions() {

  const [sessions, setSessions] = useState([]);
  const [name, setName] = useState("");

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("sessions")) || [];
    setSessions(saved);
  }, []);

  const createSession = () => {

    if (!name.trim()) return;

    const newSession = {
      id: Date.now(),
      name,
      date: new Date().toLocaleDateString(),
    };

    const updated = [...sessions, newSession];

    setSessions(updated);

    localStorage.setItem("sessions", JSON.stringify(updated));

    setName("");
  };

  const deleteSession = (id) => {

    const updated = sessions.filter((s) => s.id !== id);

    setSessions(updated);

    localStorage.setItem("sessions", JSON.stringify(updated));
  };

  return (
    <>
    <Navbar/>
    <div className="flex">
      <Sidebar/>
    <div className="max-w-4xl mx-auto mt-10">

      <h1 className="text-3xl font-bold mb-5">
        Research Sessions
      </h1>

      <div className="flex gap-3">

        <input
          type="text"
          placeholder="Session Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border p-2 rounded w-full"
        />

        <button
          onClick={createSession}
          className="bg-green-600 text-white px-4 rounded"
        >
          Create
        </button>

      </div>

      <div className="grid md:grid-cols-2 gap-4 mt-6">

        {sessions.map((session) => (
          <SessionCard
            key={session.id}
            session={session}
            onDelete={deleteSession}
          />
        ))}

      </div>
    </div>

    </div>
    </>
  );
}

export default Sessions;