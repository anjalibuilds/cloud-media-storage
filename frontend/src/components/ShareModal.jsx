import { useEffect, useState } from "react";
import {
  X,
  Share2,
  Link as LinkIcon,
  Copy,
  Check,
  Trash2,
} from "lucide-react";
import api from "../services/api";

export default function ShareModal({ file, onClose }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("viewer");
  const [shares, setShares] = useState([]);
  const [publicLinks, setPublicLinks] = useState([]);

  const [password, setPassword] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  const [loading, setLoading] = useState(false);
  const [linkLoading, setLinkLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [createdLink, setCreatedLink] = useState("");

  const loadShares = async () => {
    try {
      const response = await api.get("/shares");
      setShares(response.data || []);
    } catch (err) {
      console.error("Failed to load shares:", err);
    }
  };

  const loadPublicLinks = async () => {
    try {
      const response = await api.get("/shares/public-links");
      const links = (response.data || []).filter(
        (link) => link.file_id === file.id && link.is_active
      );
      setPublicLinks(links);
    } catch (err) {
      console.error("Failed to load public links:", err);
    }
  };

  useEffect(() => {
    loadShares();
    loadPublicLinks();
  }, [file.id]);

  const handleShare = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      await api.post("/shares", {
        file_id: file.id,
        email,
        role,
      });

      setEmail("");
      setMessage("File shared successfully.");
      await loadShares();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not share this file."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLink = async () => {
    setError("");
    setMessage("");
    setLinkLoading(true);
    setCreatedLink("");

    try {
      const payload = {
        file_id: file.id,
      };

      if (password.trim()) {
        payload.password = password;
      }

      if (expiresAt) {
        payload.expires_at = new Date(expiresAt).toISOString();
      }

      const response = await api.post(
        "/shares/public-link",
        payload
      );

      const token = response.data.token;
      const link = `${window.location.origin}/shared/${token}`;

      setCreatedLink(link);
      setPassword("");
      setExpiresAt("");
      setMessage("Public link created successfully.");

      await loadPublicLinks();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not create public link."
      );
    } finally {
      setLinkLoading(false);
    }
  };

  const handleCopy = async (link) => {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error("Copy failed:", err);
    }
  };

  const handleDeactivateLink = async (linkId) => {
    try {
      await api.delete(`/shares/public-link/${linkId}`);
      await loadPublicLinks();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not deactivate link."
      );
    }
  };

  const handleRemoveShare = async (shareId) => {
    try {
      await api.delete(`/shares/${shareId}`);
      await loadShares();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not remove share."
      );
    }
  };

  const fileShares = shares.filter(
    (share) => share.file_id === file.id
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100">
              <Share2 size={20} className="text-slate-600" />
            </div>

            <div className="min-w-0">
              <h2 className="font-bold text-slate-900">
                Share file
              </h2>

              <p className="truncate text-sm text-slate-500">
                {file.name}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-7 p-6">
          {/* Messages */}
          {message && (
            <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
              {message}
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Direct sharing */}
          <section>
            <h3 className="mb-1 text-base font-semibold">
              Share with people
            </h3>

            <p className="mb-4 text-sm text-slate-500">
              Give another registered user access to this file.
            </p>

            <form
              onSubmit={handleShare}
              className="space-y-3"
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter user's email"
                required
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-900"
              />

              <div className="flex gap-3">
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-slate-900"
                >
                  <option value="viewer">
                    Viewer — can view
                  </option>

                  <option value="editor">
                    Editor — can edit
                  </option>
                </select>

                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                >
                  {loading ? "Sharing..." : "Share"}
                </button>
              </div>
            </form>
          </section>

          {/* Existing shares */}
          {fileShares.length > 0 && (
            <section>
              <h3 className="mb-3 text-base font-semibold">
                People with access
              </h3>

              <div className="space-y-2">
                {fileShares.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-center justify-between rounded-xl border border-slate-200 p-3"
                  >
                    <div>
                      <p className="text-sm font-medium">
                        Shared user
                      </p>

                      <p className="text-xs capitalize text-slate-500">
                        {share.role}
                      </p>
                    </div>

                    <button
                      onClick={() =>
                        handleRemoveShare(share.id)
                      }
                      className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                      title="Remove access"
                    >
                      <Trash2 size={17} />
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="h-px bg-slate-200" />

          {/* Public link */}
          <section>
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100">
                <LinkIcon size={20} className="text-slate-600" />
              </div>

              <div>
                <h3 className="font-semibold">
                  Public link
                </h3>

                <p className="text-sm text-slate-500">
                  Anyone with the link can access this file.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Optional password (min 4 characters)"
                className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-900"
              />

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Optional expiry
                </label>

                <input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  min={new Date().toISOString().slice(0, 16)}
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-900"
                />
              </div>

              <button
                type="button"
                onClick={handleCreateLink}
                disabled={linkLoading}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                <LinkIcon size={17} />

                {linkLoading
                  ? "Creating link..."
                  : "Create public link"}
              </button>
            </div>
          </section>

          {/* Created link */}
          {createdLink && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Shareable link
              </p>

              <div className="flex gap-2">
                <input
                  readOnly
                  value={createdLink}
                  className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
                />

                <button
                  onClick={() => handleCopy(createdLink)}
                  className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                >
                  {copied ? (
                    <>
                      <Check size={16} />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy size={16} />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Active links */}
          {publicLinks.length > 0 && (
            <section>
              <h3 className="mb-3 text-base font-semibold">
                Active public links
              </h3>

              <div className="space-y-2">
                {publicLinks.map((link) => {
                  const shareUrl = `${window.location.origin}/shared/${link.token}`;

                  return (
                    <div
                      key={link.id}
                      className="rounded-xl border border-slate-200 p-3"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          readOnly
                          value={shareUrl}
                          className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs"
                        />

                        <button
                          onClick={() => handleCopy(shareUrl)}
                          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                        >
                          <Copy size={17} />
                        </button>

                        <button
                          onClick={() =>
                            handleDeactivateLink(link.id)
                          }
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                          title="Deactivate link"
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>

                      {link.expires_at && (
                        <p className="mt-2 text-xs text-slate-500">
                          Expires:{" "}
                          {new Date(
                            link.expires_at
                          ).toLocaleString()}
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}