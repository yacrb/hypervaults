"use client";

import Link from "next/link";
import { LogOut, ShieldCheck } from "lucide-react";

type NavbarProps = {
  email?: string;
  onLogout?: () => void;
};

export function Navbar({ email, onLogout }: NavbarProps) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 font-semibold text-ink">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-vault text-white">
            <ShieldCheck aria-hidden="true" size={19} />
          </span>
          <span>HyperVaults</span>
        </Link>
        <nav className="flex items-center gap-3 text-sm">
          {email ? (
            <>
              <span className="hidden max-w-[260px] truncate text-slate-600 sm:block">{email}</span>
              <button
                type="button"
                onClick={onLogout}
                className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 font-medium text-slate-700 hover:bg-slate-50"
              >
                <LogOut aria-hidden="true" size={16} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="rounded-md px-3 py-2 font-medium text-slate-700 hover:bg-slate-100">
                Login
              </Link>
              <Link href="/signup" className="rounded-md bg-vault px-3 py-2 font-medium text-white hover:bg-teal-800">
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
