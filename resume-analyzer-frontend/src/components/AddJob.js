import React, { useState } from "react";
import axios from "axios";

export default function AddJob() {
  const [jsonFile, setJsonFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setJsonFile(e.target.files[0]);
    setResponseData(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!jsonFile) {
      setError("Please select a JSON file first.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      // Read file content
      const text = await jsonFile.text();
      const jobs = JSON.parse(text);

      const response = await axios.post(
        "http://localhost:8000/upload_jobs_json",
        jobs,
        { headers: { "Content-Type": "application/json" } }
      );

      setResponseData(response.data);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Invalid JSON file format or upload failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-3xl bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Upload Jobs JSON
        </h2>

        <div className="flex items-center space-x-4">
          <input
            type="file"
            accept=".json"
            onChange={handleFileChange}
            className="border border-gray-300 rounded-lg px-3 py-2 w-full"
          />
          <button
            onClick={handleUpload}
            disabled={loading}
            className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </div>

        {error && <p className="text-red-500 mt-3">{error}</p>}

        {responseData && (
          <div className="mt-8 bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Response:
            </h3>
            <pre className="whitespace-pre-wrap text-gray-800">
              {JSON.stringify(responseData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
