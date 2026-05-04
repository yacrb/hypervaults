"use client";

import { useEffect, useRef } from "react";

type TurnstileApi = {
  render: (
    element: HTMLElement,
    options: {
      sitekey: string;
      callback: (token: string) => void;
      "expired-callback": () => void;
      "error-callback": () => void;
      theme: "light";
    }
  ) => string;
  reset: (widgetId: string) => void;
  remove: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

type TurnstileWidgetProps = {
  siteKey: string;
  resetSignal: number;
  onVerify: (token: string) => void;
  onExpire: () => void;
  onError: (message: string) => void;
};

const SCRIPT_ID = "cloudflare-turnstile-script";
const DEV_BYPASS_SITE_KEY = "dev-bypass";
const DEV_BYPASS_TOKEN = "dev-bypass-token";

function loadTurnstileScript(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.resolve();
  }

  if (window.turnstile) {
    return Promise.resolve();
  }

  const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Unable to load Turnstile")), { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load Turnstile"));
    document.head.appendChild(script);
  });
}

export function TurnstileWidget({ siteKey, resetSignal, onVerify, onExpire, onError }: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const widgetIdRef = useRef<string | null>(null);
  const isBypassed = siteKey === DEV_BYPASS_SITE_KEY;

  useEffect(() => {
    let cancelled = false;

    if (!siteKey) {
      onError("Turnstile site key is not configured");
      return;
    }

    if (siteKey === DEV_BYPASS_SITE_KEY) {
      onVerify(DEV_BYPASS_TOKEN);
      return;
    }

    loadTurnstileScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile || widgetIdRef.current) {
          return;
        }
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: siteKey,
          theme: "light",
          callback: onVerify,
          "expired-callback": onExpire,
          "error-callback": () => onError("Turnstile challenge failed. Try again.")
        });
      })
      .catch(() => onError("Unable to load Turnstile. Check network access or use documented local bypass."));

    return () => {
      cancelled = true;
      if (widgetIdRef.current && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current);
      }
      widgetIdRef.current = null;
    };
  }, [siteKey, onVerify, onExpire, onError]);

  useEffect(() => {
    if (siteKey === DEV_BYPASS_SITE_KEY) {
      onVerify(DEV_BYPASS_TOKEN);
      return;
    }

    if (widgetIdRef.current && window.turnstile) {
      window.turnstile.reset(widgetIdRef.current);
      onExpire();
    }
  }, [resetSignal, siteKey, onExpire, onVerify]);

  if (isBypassed) {
    return (
      <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
        Local Turnstile bypass is active.
      </div>
    );
  }

  return <div ref={containerRef} className="min-h-[70px]" />;
}
