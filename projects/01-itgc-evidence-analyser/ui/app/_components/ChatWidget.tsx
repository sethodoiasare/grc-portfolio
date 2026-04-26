"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X, Send, Plus, Loader2, Wrench } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  tool_calls?: { tool: string; input: Record<string, unknown>; result: unknown }[];
  created_at: string;
}

interface ChatSession {
  id: number;
  title: string;
  created_at: string;
}

interface Props {
  assessmentId?: number | null;
}

export function ChatWidget({ assessmentId }: Props) {
  const [open, setOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSessions, setShowSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { token } = useAuth();

  useEffect(() => {
    if (open && token) {
      fetch("/api/v1/chat/sessions", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then(setSessions)
        .catch(() => {});
    }
  }, [open, token]);

  useEffect(() => {
    if (open && assessmentId) {
      setInput(`Let's discuss assessment #${assessmentId}`);
    }
  }, [open, assessmentId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSession(id: number) {
    setActiveSession(id);
    const res = await fetch(`/api/v1/chat/sessions/${id}/messages`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setMessages(data);
    setShowSessions(false);
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);

    const optimistic: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);

    try {
      const res = await fetch("/api/v1/chat/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: activeSession, message: text }),
      });
      const data = await res.json();
      if (!activeSession) setActiveSession(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.message.content,
          tool_calls: data.message.tool_calls || undefined,
          created_at: new Date().toISOString(),
        },
      ]);

      // Refresh session list if new session created
      if (!activeSession) {
        const sl = await fetch("/api/v1/chat/sessions", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSessions(await sl.json());
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: "assistant",
          content: "Sorry, I couldn't connect to the assessor. Is the backend running?",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setActiveSession(null);
    setMessages([]);
    setShowSessions(false);
  }

  return (
    <>
      {/* Trigger button */}
      <button
        type="button"
        className="chat-trigger"
        onClick={() => setOpen(true)}
      >
        <MessageSquare size={20} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              className="chat-overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.div
              className="chat-panel"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 250 }}
            >
              {/* Header */}
              <div className="chat-header">
                <div className="chat-header-left">
                  <button
                    type="button"
                    className="chat-header-btn"
                    onClick={() => setShowSessions(!showSessions)}
                  >
                    <MessageSquare size={18} />
                  </button>
                  <span className="chat-header-title">
                    {activeSession
                      ? sessions.find((s) => s.id === activeSession)?.title || "Chat"
                      : "Assessor Chat"}
                  </span>
                </div>
                <div className="chat-header-right">
                  <button type="button" className="chat-header-btn" onClick={newChat}>
                    <Plus size={18} />
                  </button>
                  <button
                    type="button"
                    className="chat-header-btn"
                    onClick={() => setOpen(false)}
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Session list */}
              <AnimatePresence>
                {showSessions && (
                  <motion.div
                    className="chat-sessions"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                  >
                    {sessions.map((s) => (
                      <button
                        key={s.id}
                        type="button"
                        className={`chat-session-item ${activeSession === s.id ? "active" : ""}`}
                        onClick={() => loadSession(s.id)}
                      >
                        <span className="chat-session-title">{s.title}</span>
                      </button>
                    ))}
                    {sessions.length === 0 && (
                      <div className="chat-sessions-empty">No conversations yet</div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Messages */}
              <div className="chat-messages">
                {messages.length === 0 && (
                  <div className="chat-empty">
                    <MessageSquare size={32} strokeWidth={1} />
                    <p>Ask the assessor about past assessments, evidence, or to review findings.</p>
                  </div>
                )}
                {messages.map((m) => (
                  <div key={m.id} className={`chat-message ${m.role}`}>
                    <div className="chat-message-label">
                      {m.role === "user" ? "You" : "Assessor"}
                    </div>
                    <div className="chat-message-content">
                      {m.content}
                    </div>
                    {m.tool_calls && m.tool_calls.length > 0 && (
                      <div className="chat-tool-calls">
                        {m.tool_calls.map((tc, i) => (
                          <div key={i} className="chat-tool-call">
                            <Wrench size={12} />
                            <span>{tc.tool.replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="chat-message assistant">
                    <div className="chat-message-label">Assessor</div>
                    <div className="chat-typing">
                      <Loader2 size={16} className="chat-spinner" />
                      Thinking...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="chat-input-row">
                <input
                  type="text"
                  placeholder="Ask about assessments or evidence..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={sendMessage}
                  disabled={!input.trim() || loading}
                >
                  <Send size={16} />
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
