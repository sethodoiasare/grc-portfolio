import type { Metadata } from "next";
import { Outfit, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppLayout } from "./_components/AppLayout";

const outfit = Outfit({ variable: "--font-outfit", subsets: ["latin"], weight: ["300", "400", "500", "600", "700"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vuln SLA Tracker — Vodafone GRC",
  description: "Patch and vulnerability SLA breach tracking for Vodafone ITGC compliance",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${outfit.variable} ${geistMono.variable} h-full`}>
      <body className="h-full flex flex-col"><AppLayout>{children}</AppLayout></body>
    </html>
  );
}
