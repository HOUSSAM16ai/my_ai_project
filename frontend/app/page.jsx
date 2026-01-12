"use client";

import { useMemo } from "react";

const DEFAULT_LEGACY_PORT = 8000;

export default function Home() {
  const legacyUrl = useMemo(() => {
    if (process.env.NEXT_PUBLIC_LEGACY_URL) {
      return process.env.NEXT_PUBLIC_LEGACY_URL;
    }
    if (typeof window !== "undefined") {
      const protocol = window.location.protocol === "https:" ? "https" : "http";
      const hostname = window.location.hostname;
      return `${protocol}://${hostname}:${DEFAULT_LEGACY_PORT}`;
    }
    return `http://localhost:${DEFAULT_LEGACY_PORT}`;
  }, []);

  return (
    <main>
      <iframe
        src={legacyUrl}
        title="CogniForge Legacy UI"
        loading="lazy"
        referrerPolicy="no-referrer"
      />
    </main>
  );
}
