import type { Metadata } from "next";
import "./globals.css";
import { ObservatoryShell } from "../components/observatory-shell";

export const metadata: Metadata = {
  title: "Operator Observatory",
  description: "Read-only projection observability shell",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ObservatoryShell>
          {children}
        </ObservatoryShell>
      </body>
    </html>
  );
}
