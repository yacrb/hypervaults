"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { Loader2, UploadCloud } from "lucide-react";

const ALLOWED_EXTENSIONS = [".txt", ".pdf", ".png", ".jpg", ".jpeg"];
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

type FileUploaderProps = {
  onUpload: (file: File) => Promise<void>;
};

export function FileUploader({ onUpload }: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const helperText = useMemo(() => `Allowed: ${ALLOWED_EXTENSIONS.join(", ")}. Max size: 10 MB.`, []);

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setError("");
    setFile(selected);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!file) {
      setError("Choose a file first.");
      return;
    }

    const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError("This file type is not allowed.");
      return;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      setError("The file is larger than 10 MB.");
      return;
    }

    setIsUploading(true);
    setError("");
    try {
      await onUpload(file);
      setFile(null);
      form.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <label className="flex-1">
          <span className="mb-2 block text-sm font-medium text-slate-800">Upload private file</span>
          <input
            type="file"
            accept={ALLOWED_EXTENSIONS.join(",")}
            onChange={onFileChange}
            className="block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 file:mr-4 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
          />
          <span className="mt-2 block text-xs text-slate-500">{helperText}</span>
        </label>
        <button
          type="submit"
          disabled={isUploading}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-vault px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isUploading ? <Loader2 className="animate-spin" aria-hidden="true" size={17} /> : <UploadCloud aria-hidden="true" size={17} />}
          Upload
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </form>
  );
}
