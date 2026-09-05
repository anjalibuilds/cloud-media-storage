import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import { UploadCloud, X, CheckCircle, AlertCircle } from "lucide-react";
import api from "../services/api";

export default function UploadDropzone({ onUploadComplete }) {
  const [uploads, setUploads] = useState([]);

  const updateUpload = (id, data) => {
    setUploads((current) =>
      current.map((item) =>
        item.id === id ? { ...item, ...data } : item
      )
    );
  };

  const uploadFile = async (file) => {
    const uploadId = `${file.name}-${Date.now()}`;

    setUploads((current) => [
      ...current,
      {
        id: uploadId,
        name: file.name,
        progress: 0,
        status: "uploading",
        error: "",
      },
    ]);

    try {
      // Step 1: Initialize upload
      const initResponse = await api.post("/files/init-upload", {
        filename: file.name,
        mime_type: file.type,
        size: file.size,
      });

      const { file_id, storage_path, upload_url, token } =
        initResponse.data;

      // Step 2: Upload directly to Supabase Storage
      await axios.put(upload_url, file, {
        headers: {
          "Content-Type": file.type,
          "x-upsert": "false",
        },
        onUploadProgress: (event) => {
          if (!event.total) return;

          const progress = Math.round(
            (event.loaded * 100) / event.total
          );

          updateUpload(uploadId, { progress });
        },
      });

      // Step 3: Tell backend upload is complete
      const completeResponse = await api.post("/files/complete-upload", {
        file_id,
        storage_path,
        filename: file.name,
        mime_type: file.type,
        size: file.size,
      });

      updateUpload(uploadId, {
        progress: 100,
        status: "completed",
      });

      if (onUploadComplete) {
        onUploadComplete(completeResponse.data.file);
      }
    } catch (error) {
      console.error("Upload failed:", error);

      updateUpload(uploadId, {
        status: "error",
        error:
          error.response?.data?.detail ||
          "Upload failed. Please try again.",
      });
    }
  };

  const onDrop = useCallback((acceptedFiles) => {
    acceptedFiles.forEach(uploadFile);
  }, []);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    open,
  } = useDropzone({
    onDrop,
    multiple: true,
    maxSize: 50 * 1024 * 1024,
    noClick: true,
    noKeyboard: true,
  });

  const removeUpload = (id) => {
    setUploads((current) =>
      current.filter((item) => item.id !== id)
    );
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`rounded-2xl border-2 border-dashed p-10 text-center transition ${
          isDragActive
            ? "border-slate-900 bg-slate-100"
            : "border-slate-300 bg-white hover:border-slate-400"
        }`}
      >
        <input {...getInputProps()} />

        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
          <UploadCloud size={30} className="text-slate-600" />
        </div>

        <h3 className="text-lg font-semibold text-slate-800">
          {isDragActive
            ? "Drop your files here"
            : "Drag & drop files here"}
        </h3>

        <p className="mt-2 text-sm text-slate-500">
          Upload images, PDFs, videos and documents up to 50 MB
        </p>

        <button
          type="button"
          onClick={open}
          className="mt-5 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Choose Files
        </button>
      </div>

      {uploads.length > 0 && (
        <div className="space-y-3">
          {uploads.map((upload) => (
            <div
              key={upload.id}
              className="rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="flex items-center gap-3">
                {upload.status === "completed" ? (
                  <CheckCircle
                    size={20}
                    className="shrink-0 text-green-600"
                  />
                ) : upload.status === "error" ? (
                  <AlertCircle
                    size={20}
                    className="shrink-0 text-red-500"
                  />
                ) : (
                  <UploadCloud
                    size={20}
                    className="shrink-0 text-slate-500"
                  />
                )}

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-800">
                    {upload.name}
                  </p>

                  <p className="text-xs text-slate-500">
                    {upload.status === "completed"
                      ? "Upload complete"
                      : upload.status === "error"
                      ? upload.error
                      : `Uploading ${upload.progress}%`}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => removeUpload(upload.id)}
                  className="text-slate-400 hover:text-slate-700"
                >
                  <X size={18} />
                </button>
              </div>

              {upload.status === "uploading" && (
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-slate-900 transition-all duration-200"
                    style={{
                      width: `${upload.progress}%`,
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}