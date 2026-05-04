"use client";

import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LogIn } from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { TurnstileWidget } from "@/components/TurnstileWidget";
import { login } from "@/lib/api";
import { storeToken } from "@/lib/auth";

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || "";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [resetSignal, setResetSignal] = useState(0);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearTurnstile = useCallback(() => setTurnstileToken(""), []);
  const onTurnstileError = useCallback((message: string) => setError(message), []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!turnstileToken) {
      setError("Complete Turnstile verification first.");
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      const response = await login(email, password, turnstileToken);
      storeToken(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setResetSignal((value) => value + 1);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-cloud">
      <Navbar />
      <section className="mx-auto flex max-w-md flex-col px-4 py-12 sm:px-6">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-soft">
          <h1 className="text-2xl font-semibold text-ink">Log in</h1>
          <p className="mt-2 text-sm text-slate-600">Access your private HyperVaults files.</p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-800">Email</span>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2.5 text-sm text-slate-900"
              />
            </label>
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-800">Password</span>
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2.5 text-sm text-slate-900"
              />
            </label>

            <TurnstileWidget
              siteKey={TURNSTILE_SITE_KEY}
              resetSignal={resetSignal}
              onVerify={setTurnstileToken}
              onExpire={clearTurnstile}
              onError={onTurnstileError}
            />

            {error ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

            <button
              type="submit"
              disabled={isSubmitting || !turnstileToken}
              className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-vault px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? <Loader2 className="animate-spin" aria-hidden="true" size={17} /> : <LogIn aria-hidden="true" size={17} />}
              Log in
            </button>
          </form>

          <p className="mt-5 text-sm text-slate-600">
            Need an account?{" "}
            <Link href="/signup" className="font-semibold text-vault hover:text-teal-800">
              Sign up
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}
