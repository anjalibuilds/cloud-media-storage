import { useEffect, useState } from "react";
import {
  Cloud,
  Folder,
  File,
  HardDrive,
  Share2,
  Trash2,
  Star,
  LogOut,
  ChevronRight,
  Plus,
  Search,
  Upload,
  Eye,
  X,
  Download,
  ChevronLeft,
  ChevronRight as ChevronRightIcon,
} from "lucide-react";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import UploadDropzone from "../components/UploadDropzone";
import ShareModal from "../components/ShareModal";

export default function Dashboard() {
  const { user, logout } = useAuth();

  const [activeView, setActiveView] = useState("drive");

  const [files, setFiles] = useState([]);
  const [folders, setFolders] = useState([]);

  const [sharedFiles, setSharedFiles] = useState([]);

  const [loading, setLoading] = useState(true);
  const [sharedLoading, setSharedLoading] = useState(false);

  const [search, setSearch] = useState("");
  const [mimeType, setMimeType] = useState("");
  const [folderFilter, setFolderFilter] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [page, setPage] = useState(1);
  const [searchLoading, setSearchLoading] = useState(false);
  const [hasNextPage, setHasNextPage] = useState(false);

  const [showUpload, setShowUpload] = useState(false);
  const [shareFile, setShareFile] = useState(null);

  const [previewFile, setPreviewFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
const [starredFiles, setStarredFiles] = useState([]);
const [starredLoading, setStarredLoading] = useState(false);
  const [trashFiles, setTrashFiles] = useState([]);
  const [trashLoading, setTrashLoading] = useState(false);
  const [sharedError, setSharedError] = useState("");

  // =========================
  // MY DRIVE
  // =========================

  const loadDrive = async () => {
    setLoading(true);

    try {
      const [filesResponse, foldersResponse] = await Promise.all([
        api.get("/files"),
        api.get("/folders"),
      ]);

      setFiles(filesResponse.data?.files || []);
      setFolders(foldersResponse.data || []);
    } catch (error) {
      console.error("Failed to load drive:", error);
      setFiles([]);
      setFolders([]);
    } finally {
      setLoading(false);
    }
  };
  const loadStarredFiles = async () => {
  setStarredLoading(true);

  try {
    const response = await api.get("/files/starred");
    setStarredFiles(response.data?.files || []);
  } catch (error) {
    console.error("Failed to load starred files:", error);
    setStarredFiles([]);
  } finally {
    setStarredLoading(false);
  }
};

  const loadTrashFiles = async () => {
    setTrashLoading(true);
    try {
      const response = await api.get("/files/trash");
      setTrashFiles(response.data?.files || []);
    } catch (error) {
      console.error("Failed to load trash:", error);
      setTrashFiles([]);
    } finally {
      setTrashLoading(false);
    }
  };

  // =========================
  // SEARCH / FILTER / SORT
  // =========================

  const loadSearchResults = async (targetPage = page) => {
    if (activeView !== "drive") return;

    setSearchLoading(true);

    try {
      const response = await api.get("/files/search", {
        params: {
          query: search.trim() || undefined,
          mime_type: mimeType || undefined,
          folder_id: folderFilter || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
          page: targetPage,
          limit: 10,
        },
      });

      const resultFiles = response.data?.files || [];
      setFiles(resultFiles);
      setPage(response.data?.page || targetPage);
      setHasNextPage(resultFiles.length === 10);
    } catch (error) {
      console.error("Failed to search files:", error);
      setFiles([]);
      setHasNextPage(false);
    } finally {
      setSearchLoading(false);
    }
  };

  // =========================
  // SHARED FILES
  // =========================

  const loadSharedFiles = async () => {
    setSharedLoading(true);
    setSharedError("");

    try {
      const response = await api.get("/shares");

      const shares = Array.isArray(response.data)
        ? response.data
        : response.data?.shares || [];

      // Only show shares that actually contain a file.
      const filesOnly = shares.filter(
        (share) => share.file_id && share.name
      );

      setSharedFiles(filesOnly);
    } catch (error) {
      console.error("Failed to load shared files:", error);

      setSharedFiles([]);

      if (error.response?.status === 401) {
        setSharedError("Authentication required. Please sign in again.");
      } else {
        setSharedError(
          error.response?.data?.detail ||
            "Unable to load shared files."
        );
      }
    } finally {
      setSharedLoading(false);
    }
  };

  useEffect(() => {
    if (activeView === "drive") {
      loadDrive();
    }

    if (activeView === "shared") {
      loadSharedFiles();
    }

    if (activeView === "starred") {
      loadStarredFiles();
    }

    if (activeView === "trash") {
      loadTrashFiles();
    }
  }, [activeView]);

  useEffect(() => {
    if (activeView !== "drive") return;

    const timer = setTimeout(() => {
      setPage(1);
      loadSearchResults(1);
    }, 350);

    return () => clearTimeout(timer);
  }, [search, mimeType, folderFilter, sortBy, sortOrder, activeView]);

  // =========================
  // LOGOUT
  // =========================

  const handleLogout = async () => {
    await logout();
  };

  // =========================
  // UPLOAD
  // =========================

  const handleUploadComplete = () => {
    setShowUpload(false);
    loadDrive();
  };
const toggleStar = async (file) => {
  try {
    if (file.is_starred) {
      await api.delete(`/files/star/${file.id}`);
    } else {
      await api.post(`/files/star/${file.id}`);
    }

    await Promise.all([
      loadDrive(),
      loadStarredFiles(),
    ]);
  } catch (error) {
    console.error("Failed to update star:", error);
    alert(
      error.response?.data?.detail ||
        "Failed to update starred status"
    );
  }
};
  const moveToTrash = async (file) => {
    if (!window.confirm(`Move "${file.name}" to Trash?`)) return;
    try {
      await api.delete(`/files/${file.id}`);
      await Promise.all([loadDrive(), loadStarredFiles()]);
    } catch (error) {
      console.error("Failed to move file to trash:", error);
      alert(error.response?.data?.detail || "Failed to move file to trash");
    }
  };

  const restoreFromTrash = async (file) => {
    try {
      await api.post(`/files/restore/${file.id}`);
      await Promise.all([loadTrashFiles(), loadDrive()]);
    } catch (error) {
      console.error("Failed to restore file:", error);
      alert(error.response?.data?.detail || "Failed to restore file");
    }
  };

  const permanentlyDelete = async (file) => {
    if (!window.confirm(`Permanently delete "${file.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/files/permanent/${file.id}`);
      await loadTrashFiles();
    } catch (error) {
      console.error("Failed to permanently delete file:", error);
      alert(error.response?.data?.detail || "Failed to permanently delete file");
    }
  };

  // =========================
  // PREVIEW
  // =========================

  const openPreview = async (file) => {
    try {
      const response = await api.get(`/files/download/${file.id}`);

      setPreviewFile(file);
      setPreviewUrl(response.data.download_url);
    } catch (error) {
      console.error("Preview failed:", error);

      alert(
        error.response?.data?.detail ||
          "Unable to preview this file."
      );
    }
  };

  const openSharedPreview = async (share) => {
    try {
      const response = await api.get(
        `/files/download/${share.file_id}`
      );

      setPreviewFile({
        id: share.file_id,
        name: share.name,
        mime_type: share.mime_type,
        size: share.size,
      });

      setPreviewUrl(response.data.download_url);
    } catch (error) {
      console.error("Shared preview failed:", error);

      alert(
        error.response?.data?.detail ||
          "Unable to preview this shared file."
      );
    }
  };

  const closePreview = () => {
    setPreviewFile(null);
    setPreviewUrl("");
  };

  // =========================
  // SEARCH
  // =========================

  const normalizedSearch = search.toLowerCase().trim();

  const filteredFiles = files;

  const filteredFolders = folders.filter((folder) =>
    folder.name?.toLowerCase().includes(normalizedSearch)
  );

  const filteredSharedFiles = sharedFiles.filter((file) =>
    file.name?.toLowerCase().includes(normalizedSearch)
  );

  const clearFilters = () => {
    setSearch("");
    setMimeType("");
    setFolderFilter("");
    setSortBy("name");
    setSortOrder("asc");
    setPage(1);
  };

  // =========================
  // RENDER
  // =========================

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      {/* SIDEBAR */}
      <aside className="flex w-64 flex-col border-r border-slate-200 bg-white">
        <div className="flex h-20 items-center gap-3 border-b border-slate-100 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
            <Cloud size={22} />
          </div>

          <div>
            <h1 className="font-bold">Cloud Storage</h1>
            <p className="text-xs text-slate-400">
              My workspace
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-2 p-4">
          <SidebarItem
            icon={<HardDrive size={19} />}
            label="My Drive"
            active={activeView === "drive"}
            onClick={() => setActiveView("drive")}
          />

          <SidebarItem
            icon={<Share2 size={19} />}
            label="Shared"
            active={activeView === "shared"}
            onClick={() => setActiveView("shared")}
          />

          <SidebarItem
            icon={<Star size={19} />}
            label="Starred"
            active={activeView === "starred"}
            onClick={() => setActiveView("starred")}
          />

          <SidebarItem
            icon={<Trash2 size={19} />}
            label="Trash"
            active={activeView === "trash"}
            onClick={() => setActiveView("trash")}
          />
        </nav>

        <div className="border-t border-slate-100 p-4">
          <div className="mb-3 rounded-xl bg-slate-50 p-3">
            <p className="truncate text-sm font-semibold">
              {user?.full_name || "User"}
            </p>

            <p className="truncate text-xs text-slate-500">
              {user?.email}
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-600"
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="flex min-w-0 flex-1 flex-col">
        {/* HEADER */}
        <header className="flex h-20 items-center justify-between border-b border-slate-200 bg-white px-8">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <div className="relative w-full max-w-xl">
              <Search
                size={19}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
              />

              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search files and folders..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-11 pr-4 text-sm outline-none focus:border-slate-400 focus:bg-white"
              />
            </div>
          </div>

          <button
            onClick={() => setShowUpload(true)}
            className="ml-6 flex shrink-0 items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
          >
            <Plus size={18} />
            New
          </button>
        </header>

        {/* CONTENT */}
        <section className="flex-1 p-8">
          {/* BREADCRUMB */}
          <div className="mb-7 flex items-center gap-2 text-sm">
            <button
              onClick={() => setActiveView("drive")}
              className="font-semibold text-slate-900 hover:underline"
            >
              My Drive
            </button>

            <ChevronRight size={16} className="text-slate-400" />

            <span className="text-slate-500">
              {activeView === "drive"
                ? "All files"
                : activeView.charAt(0).toUpperCase() +
                  activeView.slice(1)}
            </span>
          </div>

          {activeView === "drive" && (
            <div className="mb-6 flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white p-4">
              <select
                value={mimeType}
                onChange={(e) => setMimeType(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
              >
                <option value="">All file types</option>
                <option value="application/pdf">PDF</option>
                <option value="image/jpeg">JPEG</option>
                <option value="image/png">PNG</option>
                <option value="application/msword">Word</option>
                <option value="application/vnd.openxmlformats-officedocument.wordprocessingml.document">DOCX</option>
                <option value="application/vnd.ms-excel">Excel</option>
                <option value="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">XLSX</option>
              </select>

              <select
                value={folderFilter}
                onChange={(e) => setFolderFilter(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
              >
                <option value="">All folders</option>
                {folders.map((folder) => (
                  <option key={folder.id} value={folder.id}>
                    {folder.name}
                  </option>
                ))}
              </select>

              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
              >
                <option value="name">Sort by Name</option>
                <option value="size">Sort by Size</option>
                <option value="date">Sort by Date</option>
              </select>

              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-slate-400"
              >
                <option value="asc">Ascending</option>
                <option value="desc">Descending</option>
              </select>

              {(search || mimeType || folderFilter || sortBy !== "name" || sortOrder !== "asc") && (
                <button
                  onClick={clearFilters}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  Clear filters
                </button>
              )}
            </div>
          )}

          {/* TITLE */}
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">
                {activeView === "drive"
                  ? "My Drive"
                  : activeView.charAt(0).toUpperCase() +
                    activeView.slice(1)}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {activeView === "shared"
                  ? "Files shared with you"
                  : "Manage your files and folders"}
              </p>
            </div>

            {activeView === "drive" && (
              <button
                onClick={() => setShowUpload(true)}
                className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold hover:bg-slate-50"
              >
                <Upload size={17} />
                Upload
              </button>
            )}
          </div>

          {/* =========================
              SHARED
          ========================= */}

          {activeView === "shared" ? (
            sharedLoading ? (
              <div className="flex items-center justify-center py-20 text-sm text-slate-500">
                Loading shared files...
              </div>
            ) : sharedError ? (
              <EmptyState
                icon={<Share2 size={30} />}
                title="Unable to load shared files"
                description={sharedError}
                action={
                  <button
                    onClick={loadSharedFiles}
                    className="mt-5 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white"
                  >
                    Try again
                  </button>
                }
              />
            ) : filteredSharedFiles.length === 0 ? (
              <EmptyState
                icon={<Share2 size={30} />}
                title="No shared files yet"
                description="Files shared with your account will appear here."
              />
            ) : (
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                {filteredSharedFiles.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-b-0 hover:bg-slate-50"
                  >
                    {/* ICON */}
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                      <File
                        size={20}
                        className="text-slate-600"
                      />
                    </div>

                    {/* FILE INFO */}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold">
                        {share.name}
                      </p>

                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <p className="text-xs text-slate-400">
                          {share.mime_type || "File"}
                        </p>

                        {share.owner_name && (
                          <>
                            <span className="text-xs text-slate-300">
                              •
                            </span>

                            <p className="text-xs text-slate-400">
                              Shared by {share.owner_name}
                            </p>
                          </>
                        )}

                        {share.owner_email &&
                          !share.owner_name && (
                            <>
                              <span className="text-xs text-slate-300">
                                •
                              </span>

                              <p className="text-xs text-slate-400">
                                Shared by {share.owner_email}
                              </p>
                            </>
                          )}
                      </div>
                    </div>

                    {/* SIZE */}
                    <span className="hidden text-xs text-slate-400 sm:block">
                      {share.size
                        ? `${Math.round(
                            share.size / 1024
                          )} KB`
                        : ""}
                    </span>

                    {/* ROLE */}
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        share.role === "editor"
                          ? "bg-blue-50 text-blue-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {share.role === "editor"
                        ? "Editor"
                        : "Viewer"}
                    </span>

                    {/* PREVIEW */}
                    <button
                      onClick={() =>
                        openSharedPreview(share)
                      }
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                    >
                      <Eye size={17} />
                      Preview
                    </button>
                  </div>
                ))}
              </div>
            )
          ) : activeView === "starred" ? (
            /* =========================
               STARRED
            ========================= */

            starredLoading ? (
              <div className="flex items-center justify-center py-20 text-sm text-slate-500">
                Loading starred files...
              </div>
            ) : starredFiles.filter((file) =>
                file.name?.toLowerCase().includes(normalizedSearch)
              ).length === 0 ? (
              <EmptyState
                icon={<Star size={30} />}
                title="No starred files yet"
                description="Star important files to find them quickly here."
              />
            ) : (
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                {starredFiles
                  .filter((file) =>
                    file.name?.toLowerCase().includes(normalizedSearch)
                  )
                  .map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-b-0 hover:bg-slate-50"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                        <File size={20} className="text-slate-600" />
                      </div>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold">
                          {file.name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {file.mime_type || "File"}
                        </p>
                      </div>

                      <span className="hidden text-xs text-slate-400 sm:block">
                        {file.size
                          ? `${Math.round(file.size / 1024)} KB`
                          : ""}
                      </span>

                      <button
                        onClick={() => toggleStar(file)}
                        title="Remove from Starred"
                        className="rounded-lg p-2 text-yellow-500 transition hover:bg-yellow-50"
                      >
                        <Star size={18} fill="currentColor" />
                      </button>

                      <button
                        onClick={() => openPreview(file)}
                        className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                      >
                        <Eye size={17} />
                        Preview
                      </button>
                    </div>
                  ))}
              </div>
            )
          ) : activeView === "trash" ? (
            trashLoading ? (
              <div className="flex items-center justify-center py-20 text-sm text-slate-500">
                Loading trash...
              </div>
            ) : trashFiles.filter((file) => file.name?.toLowerCase().includes(normalizedSearch)).length === 0 ? (
              <EmptyState
                icon={<Trash2 size={30} />}
                title="Trash is empty"
                description="Deleted files will appear here until you restore or permanently delete them."
              />
            ) : (
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                {trashFiles
                  .filter((file) => file.name?.toLowerCase().includes(normalizedSearch))
                  .map((file) => (
                    <div key={file.id} className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-b-0 hover:bg-slate-50">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                        <Trash2 size={20} className="text-slate-500" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold">{file.name}</p>
                        <p className="text-xs text-slate-400">
                          {file.mime_type || "File"}
                          {file.deleted_at ? ` • Deleted ${new Date(file.deleted_at).toLocaleDateString()}` : ""}
                        </p>
                      </div>
                      <span className="hidden text-xs text-slate-400 sm:block">
                        {file.size ? `${Math.round(file.size / 1024)} KB` : ""}
                      </span>
                      <button onClick={() => restoreFromTrash(file)} className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100">Restore</button>
                      <button onClick={() => permanentlyDelete(file)} className="rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50">Delete permanently</button>
                    </div>
                  ))}
              </div>
            )
          ) : searchLoading ? (
            <div className="flex items-center justify-center py-20 text-sm text-slate-500">
              Searching your files...
            </div>
          ) : loading ? (
            /* =========================
               DRIVE LOADING
            ========================= */

            <div className="flex items-center justify-center py-20 text-sm text-slate-500">
              Loading your files...
            </div>
          ) : filteredFolders.length === 0 &&
            filteredFiles.length === 0 ? (
            /* =========================
               EMPTY DRIVE
            ========================= */

            <EmptyState
              icon={<Folder size={30} />}
              title="Your drive is empty"
              description="Upload a file or create a folder to get started."
              action={
                <button
                  onClick={() => setShowUpload(true)}
                  className="mt-5 flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white"
                >
                  <Upload size={17} />
                  Upload File
                </button>
              }
            />
          ) : (
            /* =========================
               MY DRIVE CONTENT
            ========================= */

            <div className="space-y-8">
              {filteredFolders.length > 0 && (
                <div>
                  <h3 className="mb-4 text-sm font-semibold text-slate-700">
                    Folders
                  </h3>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredFolders.map((folder) => (
                      <div
                        key={folder.id}
                        className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
                          <Folder
                            size={21}
                            className="text-slate-600"
                          />
                        </div>

                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold">
                            {folder.name}
                          </p>

                          <p className="text-xs text-slate-400">
                            Folder
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {filteredFiles.length > 0 && (
                <div>
                  <h3 className="mb-4 text-sm font-semibold text-slate-700">
                    Files
                  </h3>

                  <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                    {filteredFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-b-0 hover:bg-slate-50"
                      >
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                          <File
                            size={20}
                            className="text-slate-600"
                          />
                        </div>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-semibold">
                            {file.name}
                          </p>

                          <p className="text-xs text-slate-400">
                            {file.mime_type || "File"}
                          </p>
                        </div>

                        <span className="hidden text-xs text-slate-400 sm:block">
                          {file.size
                            ? `${Math.round(
                                file.size / 1024
                              )} KB`
                            : ""}
                        </span>

                        <button
                          onClick={() => toggleStar(file)}
                          title={
                            file.is_starred
                              ? "Remove from Starred"
                              : "Add to Starred"
                          }
                          className={`rounded-lg p-2 transition ${
                            file.is_starred
                              ? "text-yellow-500 hover:bg-yellow-50"
                              : "text-slate-400 hover:bg-slate-100"
                          }`}
                        >
                          <Star
                            size={18}
                            fill={file.is_starred ? "currentColor" : "none"}
                          />
                        </button>

                        <button
                          onClick={() => openPreview(file)}
                          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                        >
                          <Eye size={17} />
                          Preview
                        </button>

                        <button
                          onClick={() => setShareFile(file)}
                          className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
                        >
                          <Share2 size={17} />
                          Share
                        </button>

                        <button
                          onClick={() => moveToTrash(file)}
                          title="Move to Trash"
                          className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeView === "drive" && !loading && !searchLoading && (files.length > 0 || page > 1) && (
            <div className="mt-6 flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3">
              <p className="text-sm text-slate-500">
                Page {page}
              </p>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const previousPage = Math.max(1, page - 1);
                    setPage(previousPage);
                    loadSearchResults(previousPage);
                  }}
                  disabled={page === 1 || searchLoading}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>

                <button
                  onClick={() => {
                    const nextPage = page + 1;
                    setPage(nextPage);
                    loadSearchResults(nextPage);
                  }}
                  disabled={!hasNextPage || searchLoading}
                  className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                  <ChevronRightIcon size={16} />
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* =========================
          UPLOAD MODAL
      ========================= */}

      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-6">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">
                  Upload Files
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Upload files directly to cloud storage.
                </p>
              </div>

              <button
                onClick={() => setShowUpload(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <UploadDropzone
              onUploadComplete={handleUploadComplete}
            />
          </div>
        </div>
      )}

      {/* =========================
          SHARE MODAL
      ========================= */}

      {shareFile && (
        <ShareModal
          file={shareFile}
          onClose={() => setShareFile(null)}
        />
      )}

      {/* =========================
          PREVIEW MODAL
      ========================= */}

      {previewFile && previewUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-6">
          <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div className="min-w-0">
                <h2 className="truncate font-semibold">
                  {previewFile.name}
                </h2>

                <p className="text-xs text-slate-500">
                  {previewFile.mime_type}
                </p>
              </div>

              <button
                onClick={closePreview}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex min-h-[500px] items-center justify-center bg-slate-100 p-4">
              {previewFile.mime_type?.startsWith(
                "image/"
              ) ? (
                <img
                  src={previewUrl}
                  alt={previewFile.name}
                  className="max-h-[75vh] max-w-full rounded-lg object-contain"
                />
              ) : previewFile.mime_type ===
                "application/pdf" ? (
                <iframe
                  src={previewUrl}
                  title={previewFile.name}
                  className="h-[75vh] w-full rounded-lg bg-white"
                />
              ) : (
                <div className="text-center">
                  <File
                    size={50}
                    className="mx-auto mb-4 text-slate-400"
                  />

                  <p className="font-semibold">
                    Preview not available
                  </p>

                  <a
                    href={previewUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white"
                  >
                    <Download size={17} />
                    Open File
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SidebarItem({
  icon,
  label,
  active,
  onClick,
}) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
        active
          ? "bg-slate-900 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function EmptyState({
  icon,
  title,
  description,
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white py-20 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
        {icon}
      </div>

      <h3 className="text-lg font-semibold text-slate-800">
        {title}
      </h3>

      <p className="mt-2 max-w-sm text-sm text-slate-500">
        {description}
      </p>

      {action}
    </div>
  );
}