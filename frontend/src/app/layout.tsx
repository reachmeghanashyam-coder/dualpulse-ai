import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DualPulse AI — Watching Over Them, So They're Never Alone",
  description: "Dual-layer hospital patient room vision sentinel powered by OpenCV 5 and AWS Graviton.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} dark`}>
      <body className="min-h-screen bg-[#09090b] text-white selection:bg-cyan-500/30 selection:text-cyan-200 antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
