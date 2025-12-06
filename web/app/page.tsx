"use client";
import { useState } from "react";

export default function Home() {
  // CS Concept: State Management
  // These variables hold the data in the browser's RAM.
  // When 'result' changes, React automatically re-renders the UI.
  const [formData, setFormData] = useState({
    reach_id: 20,
    year: 2025,
    bank: "Right",
  });

  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // The Networking Function (Client -> API)
  const handlePredict = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      // 1. Send HTTP POST Request
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("API Connection Failed");

      // 2. Parse JSON Response
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError("Failed to fetch prediction. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-900 text-white flex flex-col items-center p-10">
      <h1 className="text-4xl font-bold mb-8 text-blue-400">
        🌊 Jamuna River AI Predictor
      </h1>

      <div className="bg-slate-800 p-8 rounded-xl shadow-2xl w-full max-w-md border border-slate-700">
        {/* --- FORM SECTION --- */}
        <div className="space-y-4">

        <div>
            <label className="block text-sm font-medium mb-1">Reach ID (1-50)</label>
            <input
              type="number"
              // FIX: If state is invalid, show empty string or 0 to avoid NaN error
              value={formData.reach_id || ""}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                // FIX: If val is NaN (field cleared), set to 0, otherwise set number
                setFormData({ ...formData, reach_id: isNaN(val) ? 0 : val });
              }}
              className="w-full p-2 rounded bg-slate-700 border border-slate-600 focus:border-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Target Year</label>
            <input
              type="number"
              value={formData.year || ""}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                // FIX: Same protection here
                setFormData({ ...formData, year: isNaN(val) ? 0 : val });
              }}
              className="w-full p-2 rounded bg-slate-700 border border-slate-600 focus:border-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Bank Side</label>
            <select
              value={formData.bank}
              onChange={(e) => setFormData({ ...formData, bank: e.target.value })}
              className="w-full p-2 rounded bg-slate-700 border border-slate-600 focus:border-blue-500 outline-none"
            >
              <option value="Left">Left Bank</option>
              <option value="Right">Right Bank</option>
            </select>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading}
            className={`w-full py-3 rounded-lg font-bold transition-all ${
              loading
                ? "bg-gray-600 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 hover:shadow-lg"
            }`}
          >
            {loading ? "Calculating..." : "🔮 Predict Shift"}
          </button>
        </div>

        {/* --- ERROR MESSAGE --- */}
        {error && (
          <div className="mt-4 p-3 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm text-center">
            {error}
          </div>
        )}

        {/* --- RESULTS SECTION --- */}
        {result && (
          <div className="mt-8 animate-fade-in">
            <div className="text-center p-4 bg-slate-900 rounded-lg border border-slate-600">
              <p className="text-gray-400 text-sm uppercase tracking-wide">Predicted Shift</p>

              <div className={`text-3xl font-bold my-2 ${
                result.predicted_shift_meters < 0 ? "text-red-500" : "text-green-500"
              }`}>
                {result.predicted_shift_meters} m
              </div>

              <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                result.status === "Erosion" ? "bg-red-900 text-red-200" : "bg-green-900 text-green-200"
              }`}>
                {result.status.toUpperCase()}
              </div>
            </div>

            <div className="mt-4 text-xs text-gray-500 text-center">
              Prediction for Reach {result.reach_id} in {result.year}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
