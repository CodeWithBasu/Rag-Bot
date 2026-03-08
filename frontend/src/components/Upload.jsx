import React, { useState } from "react";
import { UploadCloud, FileText, CheckCircle, AlertCircle } from "lucide-react";
import API from "../api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle, uploading, success, error
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setStatus("idle");
  };

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    const formData = new FormData();
    formData.append("file", file);

    try {
      await API.post("/documents/upload", formData);
      setStatus("success");
      setMessage("Document processed and vectorized successfully!");
      setFile(null); // Reset after upload
    } catch (error) {
      console.error(error);
      setStatus("error");
      setMessage(error.response?.data?.detail || "Failed to upload document.");
    }
  };

  return (
    <div className="upload-container fade-in">
      <h2>Add Documents to your Brain</h2>
      <p className="subtitle">
        Upload PDFs, Word Documents, or Text files to provide context for your
        RAG Bot.
      </p>

      <div className="drag-drop-zone">
        <input
          type="file"
          id="file-upload"
          className="file-input"
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
        />
        <label htmlFor="file-upload" className="drop-label">
          <UploadCloud size={48} className="upload-icon" />
          {file ? (
            <div className="selected-file">
              <FileText size={24} />
              <span>{file.name}</span>
            </div>
          ) : (
            <span>Drag & drop or click to choose a file</span>
          )}
        </label>
      </div>

      <button
        className="btn-primary upload-btn"
        onClick={handleUpload}
        disabled={!file || status === "uploading"}
      >
        {status === "uploading"
          ? "Processing Document..."
          : "Upload & Process File"}
      </button>

      {status === "success" && (
        <div className="status-message success slide-up">
          <CheckCircle size={20} />
          <span>{message}</span>
        </div>
      )}

      {status === "error" && (
        <div className="status-message error slide-up">
          <AlertCircle size={20} />
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}
