import "./globals.css";
import type { Metadata } from "next";
import AppChrome from "./AppChrome";

export const metadata: Metadata = {
  title: "FinSight",
  description: "Fish-health diagnostic triage assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppChrome>{children}</AppChrome>
      </body>
    </html>
  );
}
