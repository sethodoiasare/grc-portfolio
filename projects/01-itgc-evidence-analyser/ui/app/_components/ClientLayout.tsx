"use client";

import { AuthProvider } from "../_hooks/useAuth";
import { AuthGuard } from "./AuthGuard";
import { TopNav } from "./TopNav";

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthGuard>
        <TopNav />
        <main className="flex-1 overflow-y-auto">{children}</main>
      </AuthGuard>
    </AuthProvider>
  );
}
