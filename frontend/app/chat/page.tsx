"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import { Message } from "@/components/MessageBubble";
import { chat } from "@/lib/api";

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [phone, setPhone] = useState("");

  // Auth guard
  useEffect(() => {
    const loggedIn = localStorage.getItem("isLoggedIn");
    if (loggedIn !== "true") {
      router.replace("/login");
      return;
    }
    setPhone(localStorage.getItem("userPhone") ?? "");
  }, [router]);

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const result = await chat(text);
      const assistantMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: result.answer,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "assistant",
          content: "⚠️ Something went wrong. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("userPhone");
    router.push("/login");
  };

  const maskedPhone = phone ? phone.slice(0, -4).replace(/./g, "•") + phone.slice(-4) : "";

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--bg-primary)" }}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0"
        style={{ background: "var(--bg-secondary)", borderColor: "var(--border)" }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-sm shadow-lg shadow-indigo-900/40">
            💸
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white">AI Expense Manager</h1>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Powered by GPT</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {phone && (
            <span className="text-xs px-2 py-1 rounded-lg" 
              style={{ background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}>
              +91 {maskedPhone}
            </span>
          )}
          <button
            id="logout-btn"
            onClick={handleLogout}
            className="text-xs px-3 py-1.5 rounded-lg font-medium transition-colors hover:opacity-80"
            style={{ background: "var(--bg-card)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Chat area */}
      <ChatWindow messages={messages} isTyping={isTyping} />

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isTyping} />
    </div>
  );
}
