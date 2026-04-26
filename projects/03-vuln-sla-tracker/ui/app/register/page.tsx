"use client";

import { useState, Suspense, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "../_hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Mail, Lock, Eye, EyeOff, ArrowLeft } from "lucide-react";

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="auth-loading"><div className="auth-loading-spinner" /></div>}>
      <RegisterForm />
    </Suspense>
  );
}

function RegisterForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { register, isAuthenticated } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const redirect = params.get("redirect") || "/";

  useEffect(() => {
    if (isAuthenticated) router.push(redirect);
  }, [isAuthenticated, redirect, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 3) { setError("Password must be at least 3 characters"); return; }
    setSubmitting(true);
    const result = await register(email, password);
    setSubmitting(false);
    if (result.error) { setError(result.error); }
    else { setSuccess(true); }
  }

  if (success) {
    return (
      <div className="login-page">
        <div className="login-card text-center">
          <h2 className="text-lg font-semibold text-[var(--pass)] mb-2">Account created</h2>
          <p className="text-sm text-[var(--muted)] mb-4">You can now sign in.</p>
          <Link href={`/login?redirect=${encodeURIComponent(redirect)}`} className="text-[var(--accent)] hover:underline text-sm">Go to login</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <motion.div className="login-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: "easeOut" }}>
        <div className="login-header">
          <Shield size={40} color="#5b8def" />
          <h1>Create Account</h1>
          <p>Register for the Vuln SLA Tracker</p>
        </div>
        {error && <motion.div className="login-error" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>{error}</motion.div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <Mail size={18} className="login-field-icon" />
            <input type="email" placeholder="Email address" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          </div>
          <div className="login-field">
            <Lock size={18} className="login-field-icon" />
            <input type={showPassword ? "text" : "password"} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="new-password" />
            <button type="button" className="login-field-toggle" onClick={() => setShowPassword(!showPassword)} tabIndex={-1}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          <button type="submit" disabled={submitting} className="login-submit">{submitting ? "Creating..." : "Create Account"}</button>
        </form>
        <p className="text-center text-xs text-[var(--muted)] mt-4">
          <Link href={`/login?redirect=${encodeURIComponent(redirect)}`} className="flex items-center justify-center gap-1 text-[var(--accent)] hover:underline">
            <ArrowLeft size={12} /> Back to login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
