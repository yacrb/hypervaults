"use client";

import { Download, FileText, Loader2, Trash2 } from "lucide-react";
import type { VaultFile } from "@/lib/api";

type FileListProps = {
  files: VaultFile[];
  busyFileId: string | null;
  onDownload: (fileId: string) => Promise<void>;
  onDelete: (fileId: string) => Promise<void>;
};

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileList({ files, busyFileId, onDownload, onDelete }: FileListProps) {
  if (files.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-600">
        No files in your vault yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-soft">
      <div className="grid grid-cols-[1fr_auto] border-b border-slate-200 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase text-slate-500 sm:grid-cols-[1fr_130px_170px_112px]">
        <span>File</span>
        <span className="hidden sm:block">Size</span>
        <span className="hidden sm:block">Uploaded</span>
        <span className="text-right">Actions</span>
      </div>
      <ul className="divide-y divide-slate-200">
        {files.map((file) => {
          const isBusy = busyFileId === file.id;
          return (
            <li
              key={file.id}
              className="grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-4 sm:grid-cols-[1fr_130px_170px_112px]"
            >
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-emerald-50 text-vault">
                  <FileText aria-hidden="true" size={18} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900">{file.original_filename}</p>
                  <p className="text-xs text-slate-500">{file.content_type}</p>
                </div>
              </div>
              <span className="hidden text-sm text-slate-600 sm:block">{formatBytes(file.size_bytes)}</span>
              <span className="hidden text-sm text-slate-600 sm:block">{new Date(file.created_at).toLocaleString()}</span>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  title="Download file"
                  disabled={isBusy}
                  onClick={() => onDownload(file.id)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isBusy ? <Loader2 className="animate-spin" aria-hidden="true" size={16} /> : <Download aria-hidden="true" size={16} />}
                </button>
                <button
                  type="button"
                  title="Delete file"
                  disabled={isBusy}
                  onClick={() => onDelete(file.id)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-red-200 text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Trash2 aria-hidden="true" size={16} />
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
