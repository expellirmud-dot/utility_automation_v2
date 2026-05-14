import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Utility Automation Governance",
  description: "Minimal SaaS dashboard for governance operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
