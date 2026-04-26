"use client";

import { usePathname } from "next/navigation";
import { AuthProvider } from "../_hooks/useAuth";
import { AuthGuard } from "./AuthGuard";
import { TopNav } from "./TopNav";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = pathname === "/login" || pathname === "/register";

  return (
    <AuthProvider>
      {isPublicPage ? (
        <>{children}</>
      ) : (
        <AuthGuard>
          <TopNav />
          <main className="flex-1 overflow-y-auto">{children}</main>
        </AuthGuard>
      )}
    </AuthProvider>
  );
}
