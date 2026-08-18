import "./globals.css";

export const metadata = {
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
      <body>{children}</body>
    </html>
  );
}
