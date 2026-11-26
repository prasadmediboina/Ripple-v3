import "./globals.css";
import type { Metadata } from "next";
import { WorkspaceProvider } from "@/lib/store";

export const metadata: Metadata = { title: "Ripple: know what a change will touch", description: "Evidence-backed change-impact analysis for pull requests." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body><WorkspaceProvider>{children}</WorkspaceProvider></body>
    </html>
  );
}
