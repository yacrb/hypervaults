"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, RefreshCcw } from "lucide-react";
import { FileList } from "@/components/FileList";
import { FileUploader } from "@/components/FileUploader";
import { Navbar } from "@/components/Navbar";
import { deleteFile, getMe, listFiles, requestDownloadUrl, uploadFile, type User, type VaultFile } from "@/lib/api";
import { clearStoredToken, getStoredToken } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [busyFileId, setBusyFileId] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const [me, vaultFiles] = await Promise.all([getMe(), listFiles()]);
      setUser(me);
      setFiles(vaultFiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load dashboard");
      if (!getStoredToken()) {
        router.replace("/login");
      }
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!getStoredToken()) {
      router.replace("/login");
      return;
    }

    let isActive = true;
    Promise.all([getMe(), listFiles()])
      .then(([me, vaultFiles]) => {
        if (!isActive) {
          return;
        }
        setUser(me);
        setFiles(vaultFiles);
      })
      .catch((err: unknown) => {
        if (!isActive) {
          return;
        }
        setError(err instanceof Error ? err.message : "Unable to load dashboard");
        if (!getStoredToken()) {
          router.replace("/login");
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [router]);

  async function onUpload(file: File) {
    const uploaded = await uploadFile(file);
    setFiles((current) => [uploaded, ...current]);
  }

  async function onDownload(fileId: string) {
    setBusyFileId(fileId);
    setError("");
    try {
      const response = await requestDownloadUrl(fileId);
      window.location.assign(response.download_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create download link");
    } finally {
      setBusyFileId(null);
    }
  }

  async function onDelete(fileId: string) {
    setBusyFileId(fileId);
    setError("");
    try {
      await deleteFile(fileId);
      setFiles((current) => current.filter((file) => file.id !== fileId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete file");
    } finally {
      setBusyFileId(null);
    }
  }

  function onLogout() {
    clearStoredToken();
    router.push("/login");
  }

  return (
    <main className="min-h-screen bg-cloud">
      <Navbar email={user?.email} onLogout={onLogout} />
      <section className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-3xl font-semibold text-ink">Dashboard</h1>
            <p className="mt-2 text-sm text-slate-600">Upload, retrieve, and remove files owned by your account.</p>
          </div>
          <button
            type="button"
            onClick={() => void loadDashboard()}
            className="inline-flex items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCcw aria-hidden="true" size={16} />
            Refresh
          </button>
        </div>

        {error ? <p className="mb-5 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
            <p className="text-xs font-semibold uppercase text-slate-500">Account</p>
            <p className="mt-2 truncate text-sm font-medium text-slate-900">{user?.email ?? "Loading"}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
            <p className="text-xs font-semibold uppercase text-slate-500">Files</p>
            <p className="mt-2 text-sm font-medium text-slate-900">{files.length}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-soft">
            <p className="text-xs font-semibold uppercase text-slate-500">Download links</p>
            <p className="mt-2 text-sm font-medium text-slate-900">Short-lived</p>
          </div>
        </div>

        <div className="space-y-6">
          <FileUploader onUpload={onUpload} />

          {isLoading ? (
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-soft">
              <Loader2 className="animate-spin" aria-hidden="true" size={18} />
              Loading vault
            </div>
          ) : (
            <FileList files={files} busyFileId={busyFileId} onDownload={onDownload} onDelete={onDelete} />
          )}
        </div>
      </section>
    </main>
  );
}
