import { useState } from "react";
import { useParams } from "react-router-dom";
import { Cloud, Eye, Lock, File } from "lucide-react";
import api from "../services/api";

export default function PublicShare() {
  const { token } = useParams();

  const [password, setPassword] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [unlocked, setUnlocked] = useState(false);

  const accessLink = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.post(
        `/shares/public-link/${token}/access`,
        {
          password: password || null,
        }
      );

      setFile(response.data);
      setUnlocked(true);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to access this shared file."
      );
    } finally {
      setLoading(false);
    }
  };

  if (unlocked && file?.download_url) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <header className="flex h-20 items-center gap-3 border-b border-slate-200 bg-white px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
            <Cloud size={22} />
          </div>

          <div>
            <h1 className="font-bold">Cloud Storage</h1>
            <p className="text-xs text-slate-400">
              Public shared file
            </p>
          </div>
        </header>

        <main className="mx-auto max-w-5xl p-6 md:p-10">
          <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100">
                <File size={22} className="text-slate-600" />
              </div>

              <div className="min-w-0">
                <h2 className="truncate font-semibold">
                  {file.name}
                </h2>

                <p className="text-sm text-slate-500">
                  {file.mime_type} •{" "}
                  {file.size
                    ? `${Math.round(file.size / 1024)} KB`
                    : ""}
                </p>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-4">
            {file.mime_type === "application/pdf" ? (
              <iframe
                src={file.download_url}
                title={file.name}
                className="h-[75vh] w-full rounded-xl"
              />
            ) : file.mime_type?.startsWith("image/") ? (
              <div className="flex min-h-[500px] items-center justify-center bg-slate-50">
                <img
                  src={file.download_url}
                  alt={file.name}
                  className="max-h-[70vh] max-w-full rounded-xl object-contain"
                />
              </div>
            ) : (
              <div className="flex min-h-[400px] flex-col items-center justify-center">
                <File
                  size={50}
                  className="mb-4 text-slate-400"
                />

                <p className="mb-4 font-semibold">
                  Preview not available
                </p>

                <a
                  href={file.download_url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white"
                >
                  Open File
                </a>
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-5">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex justify-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <Lock size={25} />
          </div>
        </div>

        <h1 className="text-center text-2xl font-bold">
          Shared File
        </h1>

        <p className="mt-2 text-center text-sm text-slate-500">
          Someone shared a file with you.
        </p>

        {error && (
          <div className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        <div className="mt-6">
          <label className="mb-2 block text-sm font-medium">
            Password
          </label>

          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                accessLink();
              }
            }}
            placeholder="Enter password if required"
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-slate-400"
          />
        </div>

        <button
          onClick={accessLink}
          disabled={loading}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
        >
          <Eye size={17} />
          {loading ? "Opening..." : "Open Shared File"}
        </button>
      </div>
    </div>
  );
}