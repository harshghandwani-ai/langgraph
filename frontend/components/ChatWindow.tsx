"use client";
import { useEffect, useRef } from "react";
import MessageBubble, { Message } from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
  isTyping: boolean;
}

function TypingIndicator() {
  return (
    <div className="flex items-start gap-2 mb-4 msg-enter">
      <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>
        💸
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-1.5"
        style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>
        <div className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
        <div className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
        <div className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
      </div>
    </div>
  );
}

function EmptyState() {
  const suggestions = [
    "I spent 500 on groceries today",
    "Paid 1200 for electricity bill via UPI",
    "How much did I spend this month?",
    "Show my last 5 expenses",
  ];
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="text-5xl mb-4">💸</div>
      <h2 className="text-xl font-semibold mb-2 gradient-text">AI Expense Manager</h2>
      <p className="text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
        Log expenses or ask about your spending — in plain English.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
        {suggestions.map((s) => (
          <div key={s} className="px-3 py-2.5 rounded-xl text-xs text-left cursor-default transition-colors"
            style={{ background: "var(--bg-card)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}>
            "{s}"
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, isTyping }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 chat-scroll" style={{ background: "var(--bg-primary)" }}>
      <div className="max-w-3xl mx-auto">
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
