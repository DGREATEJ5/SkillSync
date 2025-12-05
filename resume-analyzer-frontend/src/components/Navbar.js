import React from "react";

export default function Navbar({ currentTab, setCurrentTab }) {
  return (
    <nav className="bg-blue-600 text-white px-6 py-4 flex justify-between items-center">
      <div className="text-xl font-bold">SkillSync</div>
      <div className="space-x-4">
        <button
          className={`px-3 py-1 rounded ${currentTab === "resume" ? "bg-white text-blue-600" : ""}`}
          onClick={() => setCurrentTab("resume")}
        >
          Upload Resume
        </button>
        <button
          className={`px-3 py-1 rounded ${currentTab === "job" ? "bg-white text-blue-600" : ""}`}
          onClick={() => setCurrentTab("job")}
        >
          Add Job
        </button>
      </div>
    </nav>
  );
}
