"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Plus } from "lucide-react";
import { useAuth } from "../_hooks/useAuth";

interface Props {
  marketId: number | null;
  controlId: string;
  tags: string[];
  onChange: (tags: string[]) => void;
}

export function SampleEditor({ marketId, controlId, tags, onChange }: Props) {
  const [input, setInput] = useState("");
  const [saved, setSaved] = useState(false);
  const { token } = useAuth();

  // Load saved samples when marketId/controlId change
  useEffect(() => {
    if (!marketId || !controlId) return;
    fetch(`/api/v1/samples?market_id=${marketId}&control_id=${encodeURIComponent(controlId)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.tags && data.tags.length > 0) {
          onChange(data.tags);
        }
      })
      .catch(() => {});
  }, [marketId, controlId]);

  const persistSamples = useCallback(
    async (newTags: string[]) => {
      if (!marketId || !controlId || !token) return;
      try {
        await fetch("/api/v1/samples", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ market_id: marketId, control_id: controlId, tags: newTags }),
        });
        setSaved(true);
        setTimeout(() => setSaved(false), 1500);
      } catch {}
    },
    [marketId, controlId, token]
  );

  function addTag() {
    const trimmed = input.trim();
    if (!trimmed || tags.includes(trimmed)) {
      setInput("");
      return;
    }
    const newTags = [...tags, trimmed];
    onChange(newTags);
    persistSamples(newTags);
    setInput("");
  }

  function removeTag(index: number) {
    const newTags = tags.filter((_, i) => i !== index);
    onChange(newTags);
    persistSamples(newTags);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag();
    }
  }

  return (
    <div className="sample-editor">
      <div className="sample-editor-tags">
        {tags.map((tag, i) => (
          <span key={i} className="sample-tag">
            {tag}
            <button type="button" onClick={() => removeTag(i)}>
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <div className="sample-editor-input-row">
        <input
          type="text"
          placeholder="Add a sample (e.g. Phones)..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button type="button" onClick={addTag} disabled={!input.trim()}>
          <Plus size={16} />
        </button>
        {saved && <span className="sample-saved">Saved</span>}
      </div>
    </div>
  );
}
