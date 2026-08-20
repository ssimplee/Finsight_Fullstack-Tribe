"use client";

import { usePathname } from "next/navigation";
import Header from "../components/layout/Header";
import { ConsultationProvider } from "../context/ConsultationContext";

export default function AppChrome({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  return (
    <ConsultationProvider>
      <div className="app-shell">
        <Header currentPath={pathname} />
        {children}
      </div>
    </ConsultationProvider>
  );
}
