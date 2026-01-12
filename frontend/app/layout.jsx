import "./globals.css";

export const metadata = {
  title: "CogniForge Next Gateway",
  description: "Next.js shell for the CogniForge legacy UI."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
