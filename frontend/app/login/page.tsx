import LoginForm from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-12" 
      style={{ background: "var(--bg-primary)" }}>
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 rounded-full opacity-20 blur-3xl"
          style={{ background: "radial-gradient(circle, #4f46e5, transparent)" }} />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 rounded-full opacity-15 blur-3xl"
          style={{ background: "radial-gradient(circle, #7c3aed, transparent)" }} />
      </div>

      <div className="relative z-10 w-full flex flex-col items-center gap-6 max-w-sm">
        <LoginForm />
        <p className="text-xs text-center" style={{ color: "var(--text-secondary)" }}>
          Demo mode · No real authentication
        </p>
      </div>
    </main>
  );
}
