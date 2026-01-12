"use client";

import { useEffect, useMemo, useState } from "react";

const LEGACY_SCRIPTS = [
  {
    id: "legacy-react",
    src: "https://cdn.jsdelivr.net/npm/react@17/umd/react.production.min.js"
  },
  {
    id: "legacy-react-dom",
    src: "https://cdn.jsdelivr.net/npm/react-dom@17/umd/react-dom.production.min.js"
  },
  {
    id: "legacy-babel",
    src: "https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js"
  },
  {
    id: "legacy-showdown",
    src: "https://cdn.jsdelivr.net/npm/showdown/dist/showdown.min.js"
  },
  {
    id: "legacy-axios",
    src: "https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"
  },
  {
    id: "legacy-performance",
    src: "/performance-monitor.js"
  }
];

const LEGACY_APP_SCRIPT = {
  id: "legacy-app",
  src: "/js/legacy-app.jsx",
  type: "text/babel",
  attributes: { "data-presets": "env,react" }
};

const ensureScript = (script) =>
  new Promise((resolve, reject) => {
    if (typeof window === "undefined") {
      resolve();
      return;
    }

    if (document.getElementById(script.id)) {
      resolve();
      return;
    }

    const existing = document.querySelector(`script[src="${script.src}"]`);
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener(
        "error",
        () => reject(new Error(`Failed to load ${script.src}`)),
        { once: true }
      );
      return;
    }

    const element = document.createElement("script");
    element.id = script.id;
    element.src = script.src;
    element.async = false;

    if (script.type) {
      element.type = script.type;
    }

    if (script.attributes) {
      Object.entries(script.attributes).forEach(([key, value]) => {
        element.setAttribute(key, value);
      });
    }

    element.addEventListener("load", resolve, { once: true });
    element.addEventListener(
      "error",
      () => reject(new Error(`Failed to load ${script.src}`)),
      { once: true }
    );

    document.head.appendChild(element);
  });

export default function LegacyLoader() {
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  const loadingMessage = useMemo(() => {
    if (status === "error") {
      return "تعذر تحميل الواجهة. يرجى إعادة المحاولة.";
    }
    return "جارٍ تشغيل واجهة CogniForge...";
  }, [status]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (window.__legacyAppLoaded || window.__legacyAppLoading) {
      setStatus("ready");
      return;
    }

    window.__legacyAppLoading = true;

    const load = async () => {
      try {
        for (const script of LEGACY_SCRIPTS) {
          await ensureScript(script);
        }
        await ensureScript(LEGACY_APP_SCRIPT);
        window.__legacyAppLoaded = true;
        setStatus("ready");
      } catch (loadError) {
        console.error(loadError);
        setError(loadError);
        setStatus("error");
      } finally {
        window.__legacyAppLoading = false;
      }
    };

    load();
  }, []);

  if (status === "ready") {
    return null;
  }

  return (
    <div aria-live="polite" className="legacy-loader">
      <p>{loadingMessage}</p>
      {error ? (
        <p className="legacy-loader__error">{String(error.message || error)}</p>
      ) : null}
    </div>
  );
}
