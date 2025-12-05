import React, { useState } from "react";
import axios from "axios";

const UploadResume = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [responseData, setResponseData] = useState(null);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResponseData(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://localhost:8000/upload_resume",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResponseData(response.data);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Error uploading file. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-3xl bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Upload Resume
        </h2>

        <div className="flex items-center space-x-4">
          <input
            type="file"
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
          <div className="mt-8 space-y-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Recommendation:
              </h3>
              <p className="bg-gray-50 p-4 rounded-lg border border-gray-200 whitespace-pre-wrap">
                {responseData.recommendation}
              </p>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">
                Job Matches:
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-600">ID</th>
                      <th className="px-4 py-2 text-left text-gray-600">Title</th>
                      <th className="px-4 py-2 text-left text-gray-600">Description</th>
                      <th className="px-4 py-2 text-left text-gray-600">Skills</th>
                      <th className="px-4 py-2 text-left text-gray-600">Matched Skills</th>
                      <th className="px-4 py-2 text-left text-gray-600">Semantic Score</th>
                      <th className="px-4 py-2 text-left text-gray-600">Keyword Score</th>
                      <th className="px-4 py-2 text-left text-gray-600">Final Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {responseData.matches.map((match) => (
                      <tr key={match.id} className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="px-4 py-2">{match.id}</td>
                        <td className="px-4 py-2 font-medium">{match.title}</td>
                        <td className="px-4 py-2">{match.description}</td>
                        <td className="px-4 py-2">{match.skills.join(", ")}</td>
                        <td className="px-4 py-2">{match.matched_skills.join(", ")}</td>
                        <td className="px-4 py-2">{match.semantic_score.toFixed(3)}</td>
                        <td className="px-4 py-2">{match.keyword_score}</td>
                        <td className="px-4 py-2">{match.final_score.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadResume;
