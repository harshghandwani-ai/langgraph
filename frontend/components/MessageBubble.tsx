export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const time = message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className={`flex msg-enter ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      {/* Avatar — assistant only */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm mr-2 mt-1"
          style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}>
          💸
        </div>
      )}

      <div className={`flex flex-col ${isUser ? "items-end" : "items-start"} max-w-[80%]`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-md ${
            isUser
              ? "rounded-tr-sm text-white"
              : "rounded-tl-sm"
          }`}
          style={
            isUser
              ? { background: "linear-gradient(135deg, #4f46e5, #6d28d9)", color: "#fff" }
              : { background: "var(--bg-card)", color: "var(--text-primary)", border: "1px solid var(--border)" }
          }
        >
          {message.content}
        </div>
        <span className="text-xs mt-1 px-1" style={{ color: "var(--text-secondary)" }}>
          {time}
        </span>
      </div>

      {/* Avatar — user only */}
      {isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-sm ml-2 mt-1"
          style={{ background: "var(--user-bubble)", border: "1px solid rgba(255,255,255,0.1)" }}>
          👤
        </div>
      )}
    </div>
  );
}
