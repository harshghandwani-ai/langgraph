"use client";
import { useState, KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-4 border-t" style={{ borderColor: "var(--border)", background: "var(--bg-secondary)" }}>
      <div className="max-w-3xl mx-auto flex gap-3 items-end">
        <div
          className="flex-1 rounded-2xl border transition-all focus-within:border-indigo-500 px-4 py-3"
          style={{ background: "var(--bg-primary)", borderColor: "var(--border)" }}
        >
          <textarea
            id="chat-input"
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKey}
            disabled={disabled}
            placeholder="Ask or log an expense…"
            className="w-full bg-transparent text-sm outline-none resize-none placeholder-slate-500 leading-relaxed"
            style={{
              color: "var(--text-primary)",
              maxHeight: "120px",
              overflowY: "auto",
            }}
          />
        </div>

        <button
          id="send-btn"
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-200 active:scale-90 disabled:opacity-40"
          style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
          title="Send (Enter)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-white -rotate-45 translate-x-0.5">
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        </button>
      </div>
      <p className="text-center text-xs mt-2" style={{ color: "var(--text-secondary)" }}>
        Press <kbd className="px-1 rounded font-mono text-xs" style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>Enter</kbd> to send · <kbd className="px-1 rounded font-mono text-xs" style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
