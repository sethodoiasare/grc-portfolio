"use client";

import { useAuth } from "../_hooks/useAuth";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !isAuthenticated && pathname !== "/login") {
      router.push("/login?redirect=" + encodeURIComponent(pathname));
    }
  }, [loading, isAuthenticated, pathname, router]);

  if (loading) {
    return <div className="auth-loading"><div className="auth-loading-spinner" /></div>;
  }
  if (!isAuthenticated && pathname !== "/login") return null;
  return <>{children}</>;
}
