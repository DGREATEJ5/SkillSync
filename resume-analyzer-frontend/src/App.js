import React, { useState } from "react";
import Navbar from "./components/Navbar";
import UploadResume from "./components/UploadResume";
import AddJob from "./components/AddJob";

function App() {
  const [currentTab, setCurrentTab] = useState("resume");

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      {currentTab === "resume" && <UploadResume />}
      {currentTab === "job" && <AddJob />}
    </div>
  );
}

export default App;
