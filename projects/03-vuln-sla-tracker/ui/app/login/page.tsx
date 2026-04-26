"use client";

import { useState, Suspense, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../_hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Mail, Lock, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="auth-loading"><div className="auth-loading-spinner" /></div>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const redirect = params.get("redirect") || "/";

  useEffect(() => {
    if (isAuthenticated) router.push(redirect);
  }, [isAuthenticated, redirect, router]);

  if (isAuthenticated) {
    return <div className="auth-loading"><div className="auth-loading-spinner" /></div>;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const result = await login(email, password);
    setSubmitting(false);
    if (result.error) { setError(result.error); }
    else { router.push(redirect); }
  }

  return (
    <div className="login-page">
      <motion.div className="login-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: "easeOut" }}>
        <div className="login-header">
          <Shield size={40} color="#5b8def" />
          <h1>Vuln SLA Tracker</h1>
          <p>Sign in to your auditor account</p>
        </div>
        {error && <motion.div className="login-error" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>{error}</motion.div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <Mail size={18} className="login-field-icon" />
            <input type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </div>
          <div className="login-field">
            <Lock size={18} className="login-field-icon" />
            <input type={showPassword ? "text" : "password"} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
            <button type="button" className="login-field-toggle" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <button type="submit" disabled={submitting} className="login-submit">{submitting ? "Signing in..." : "Sign In"}</button>
        </form>
        <p className="text-center text-xs text-[var(--muted)] mt-4">
          Don&apos;t have an account?{" "}
          <Link href={`/register${redirect !== "/" ? `?redirect=${encodeURIComponent(redirect)}` : ""}`} className="text-[var(--accent)] hover:underline">Create one</Link>
        </p>
      </motion.div>
    </div>
  );
}
