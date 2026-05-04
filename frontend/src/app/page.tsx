import Link from "next/link";
import { ArrowRight, FileLock2, Server, ShieldCheck } from "lucide-react";
import { Navbar } from "@/components/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen bg-cloud">
      <Navbar />
      <section className="mx-auto grid max-w-6xl gap-10 px-4 py-14 sm:px-6 lg:grid-cols-[1fr_0.9fr] lg:px-8 lg:py-20">
        <div className="flex flex-col justify-center">
          <p className="mb-4 text-sm font-semibold uppercase text-vault">Secure team document vault</p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-normal text-ink sm:text-5xl">
            HyperVaults keeps private files scoped to the people who own them.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Sign up, verify with Turnstile, upload approved document types, and retrieve files through short-lived private download links.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-vault px-5 py-3 text-sm font-semibold text-white hover:bg-teal-800"
            >
              Create vault
              <ArrowRight aria-hidden="true" size={17} />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-50"
            >
              Log in
            </Link>
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
          <div className="mb-5 flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <p className="text-sm font-semibold text-ink">Team Vault</p>
              <p className="text-xs text-slate-500">Private bucket, verified access</p>
            </div>
            <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-vault">Online</span>
          </div>
          <div className="space-y-3">
            {[
              ["Board-Minutes.pdf", "application/pdf", "Encrypted path users/{id}/..."],
              ["Roadmap.txt", "text/plain", "Owner checked before download"],
              ["Architecture.png", "image/png", "Presigned URL expires quickly"]
            ].map(([name, type, note]) => (
              <div key={name} className="flex items-center gap-3 rounded-md border border-slate-200 p-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-slate-100 text-vault">
                  <FileLock2 aria-hidden="true" size={18} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-900">{name}</p>
                  <p className="text-xs text-slate-500">{type}</p>
                </div>
                <span className="hidden max-w-[160px] text-right text-xs text-slate-500 sm:block">{note}</span>
              </div>
            ))}
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-slate-200 p-4">
              <ShieldCheck aria-hidden="true" className="mb-3 text-vault" size={20} />
              <p className="text-sm font-semibold text-ink">Server-side checks</p>
              <p className="mt-1 text-sm text-slate-600">JWT auth and ownership filtering protect every file route.</p>
            </div>
            <div className="rounded-md border border-slate-200 p-4">
              <Server aria-hidden="true" className="mb-3 text-vault" size={20} />
              <p className="text-sm font-semibold text-ink">Local stack</p>
              <p className="mt-1 text-sm text-slate-600">Next.js, FastAPI, PostgreSQL, MinIO, and Nginx.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
