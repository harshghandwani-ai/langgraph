import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

/** Log a new expense from natural-language text */
export async function logExpense(text: string): Promise<string> {
  const res = await client.post("/api/expenses", { text });
  return res.data;
}

/** Query past expenses in natural language */
export async function queryExpense(query: string): Promise<string> {
  const res = await client.post("/api/expenses/query", { question: query });
  return res.data.answer;
}

/** Unified chat — send to /api/chat which routes LOG / QUERY / CHAT automatically */
export async function chat(message: string): Promise<{ intent: string; answer: string }> {
  console.log("Chatting with:", `${API_BASE}/api/chat`, "message:", message);
  try {
    const res = await client.post("/api/chat", { message });
    console.log("Chat response:", res.data);
    return res.data; // { intent, answer, expense? }
  } catch (error) {
    console.error("Chat error:", error);
    throw error;
  }
}

// ─── Export axios client for extensibility ────────────────────────────────────
export { client };
