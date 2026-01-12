"use client";

import Script from "next/script";

export default function Home() {
  return (
    <main>
      <div id="root"></div>
      <Script
        src="https://cdn.jsdelivr.net/npm/react@17/umd/react.production.min.js"
        strategy="beforeInteractive"
      />
      <Script
        src="https://cdn.jsdelivr.net/npm/react-dom@17/umd/react-dom.production.min.js"
        strategy="beforeInteractive"
      />
      <Script
        src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js"
        strategy="beforeInteractive"
      />
      <Script
        src="https://cdn.jsdelivr.net/npm/showdown/dist/showdown.min.js"
        strategy="afterInteractive"
      />
      <Script
        src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"
        strategy="afterInteractive"
      />
      <Script src="/performance-monitor.js" strategy="afterInteractive" />
      <Script
        src="/js/legacy-app.jsx"
        type="text/babel"
        strategy="afterInteractive"
      />
    </main>
  );
}
