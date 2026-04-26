"use client";

import { useState, Suspense, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Shield, Mail, Lock, Eye, EyeOff, UserPlus } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

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
  const { register, isAuthenticated, login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const redirect = params.get("redirect") || "/";

  useEffect(() => {
    if (isAuthenticated) {
      router.push(redirect);
    }
  }, [isAuthenticated, redirect, router]);

  if (isAuthenticated) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner" />
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const result = await register(email, password);
    setSubmitting(false);
    if (result.error) {
      setError(result.error);
    } else {
      // Auto-login after registration
      const loginResult = await login(email, password);
      if (loginResult.error) {
        setSuccess(true);
      } else {
        router.push(redirect);
      }
    }
  }

  if (success) {
    return (
      <div className="login-page">
        <motion.div
          className="login-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="login-header">
            <UserPlus size={40} color="#26c963" />
            <h1>Account Created</h1>
            <p>Your auditor account is ready. Sign in below.</p>
          </div>
          <Link href="/login" className="login-submit" style={{ display: "block", textAlign: "center", textDecoration: "none" }}>
            Go to Sign In
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="login-page">
      <motion.div
        className="login-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        <div className="login-header">
          <Shield size={40} color="#E60000" />
          <h1>Create Account</h1>
          <p>Join as an auditor on the ITGC Evidence Analyser</p>
        </div>

        {error && (
          <motion.div
            className="login-error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <Mail size={18} className="login-field-icon" />
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <Lock size={18} className="login-field-icon" />
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              minLength={6}
            />
            <button
              type="button"
              className="login-field-toggle"
              onClick={() => setShowPassword(!showPassword)}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button type="submit" disabled={submitting} className="login-submit">
            {submitting ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-xs text-[var(--muted)] mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-[var(--accent)] hover:underline">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
