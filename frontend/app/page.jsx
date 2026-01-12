"use client";

import CogniForgeApp from "./components/CogniForgeApp";
import Script from "next/script";

export default function Home() {
  return (
    <main>
       {/* Load font awesome as it was used in legacy app */}
       <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
       {/* Load legacy CSS */}
       <link rel="stylesheet" href="/css/styles.css" />

       <CogniForgeApp />

       <Script src="/performance-monitor.js" strategy="afterInteractive" />
    </main>
  );
}
