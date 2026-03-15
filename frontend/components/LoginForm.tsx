"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import OtpInput from "./OtpInput";

export default function LoginForm() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSendOtp = () => {
    const cleaned = phone.replace(/\D/g, "");
    if (cleaned.length < 10) {
      setError("Please enter a valid 10-digit phone number.");
      return;
    }
    setError("");
    setLoading(true);
    // Simulate OTP send delay
    setTimeout(() => {
      setLoading(false);
      setStep("otp");
    }, 800);
  };

  const handleVerifyOtp = (otp: string) => {
    if (otp.length !== 4) return;
    setLoading(true);
    setTimeout(() => {
      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("userPhone", phone);
      router.push("/chat");
    }, 600);
  };

  return (
    <div className="glass rounded-2xl p-8 w-full max-w-sm shadow-2xl">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-indigo-900/50">
          💸
        </div>
        <div>
          <h1 className="text-lg font-semibold text-white">AI Expense Manager</h1>
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>Smart spending, powered by AI</p>
        </div>
      </div>

      {step === "phone" ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
              Phone Number
            </label>
            <div className="flex gap-2 items-center rounded-xl border px-3 py-3 transition-all focus-within:border-indigo-500"
              style={{ background: "var(--bg-primary)", borderColor: "var(--border)" }}>
              <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>+91</span>
              <div className="w-px h-4 mx-1" style={{ background: "var(--border)" }} />
              <input
                id="phone-input"
                type="tel"
                maxLength={10}
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))}
                onKeyDown={(e) => e.key === "Enter" && handleSendOtp()}
                placeholder="Enter phone number"
                className="flex-1 bg-transparent text-sm outline-none placeholder-slate-500"
                style={{ color: "var(--text-primary)" }}
              />
            </div>
            {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
          </div>

          <button
            id="send-otp-btn"
            onClick={handleSendOtp}
            disabled={loading}
            className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200 active:scale-95 disabled:opacity-60"
            style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
          >
            {loading ? "Sending…" : "Send OTP"}
          </button>
        </div>
      ) : (
        <OtpInput phone={phone} onVerify={handleVerifyOtp} loading={loading} />
      )}
    </div>
  );
}
