"use client";
import { useState, useRef, KeyboardEvent, ChangeEvent } from "react";

interface OtpInputProps {
  phone: string;
  onVerify: (otp: string) => void;
  loading: boolean;
}

export default function OtpInput({ phone, onVerify, loading }: OtpInputProps) {
  const [digits, setDigits] = useState(["", "", "", ""]);
  const refs = [
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
  ];

  const handleChange = (index: number, e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[index] = val;
    setDigits(next);
    if (val && index < 3) refs[index + 1].current?.focus();
    if (next.every((d) => d) && next.join("").length === 4) {
      onVerify(next.join(""));
    }
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      refs[index - 1].current?.focus();
    }
  };

  const maskedPhone = phone.slice(0, -4).replace(/./g, "•") + phone.slice(-4);

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm mb-1" style={{ color: "var(--text-secondary)" }}>OTP sent to</p>
        <p className="font-semibold text-white">+91 {maskedPhone}</p>
      </div>

      <div>
        <label className="block text-sm font-medium mb-3" style={{ color: "var(--text-secondary)" }}>
          Enter 4-digit OTP
        </label>
        <div className="flex gap-3 justify-center">
          {digits.map((d, i) => (
            <input
              key={i}
              id={`otp-${i}`}
              ref={refs[i]}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={d}
              onChange={(e) => handleChange(i, e)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              autoFocus={i === 0}
              className="w-14 h-14 text-center text-xl font-bold rounded-xl border outline-none transition-all focus:border-indigo-500 focus:shadow-lg focus:shadow-indigo-900/30"
              style={{
                background: "var(--bg-primary)",
                borderColor: d ? "#4f46e5" : "var(--border)",
                color: "var(--text-primary)",
              }}
            />
          ))}
        </div>
        <p className="text-center text-xs mt-3" style={{ color: "var(--text-secondary)" }}>
          Any 4-digit code works for demo
        </p>
      </div>

      <button
        id="verify-otp-btn"
        onClick={() => onVerify(digits.join(""))}
        disabled={loading || digits.join("").length !== 4}
        className="w-full py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200 active:scale-95 disabled:opacity-40"
        style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
      >
        {loading ? "Verifying…" : "Verify & Continue →"}
      </button>
    </div>
  );
}
