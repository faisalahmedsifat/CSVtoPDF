"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setPdfUrl(null); // Reset the PDF link if a new file is selected
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!file) {
      setError("Please upload a CSV file.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append("csv_file", file);

    try {
      const response = await fetch("http:///generate_pdf/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to generate PDF. Please try again.");
      }

      const blob = await response.blob();
      const pdfUrl = window.URL.createObjectURL(blob);
      setPdfUrl(pdfUrl);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-5">
      <h1 className="text-3xl font-bold mb-8">Upload CSV and Download PDF</h1>

      <form onSubmit={handleSubmit} className="flex flex-col items-center">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="mb-4"
        />
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded"
          disabled={loading}
        >
          {loading ? "Uploading..." : "Upload CSV and Generate PDF"}
        </button>
      </form>

      {pdfUrl && (
        <div className="mt-6">
          <a
            href={pdfUrl}
            download="generated_pdf.pdf"
            className="bg-green-500 text-white px-4 py-2 rounded"
          >
            Download PDF
          </a>
        </div>
      )}
    </div>
  );
}
