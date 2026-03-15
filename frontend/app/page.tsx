"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const loggedIn = localStorage.getItem("isLoggedIn");
    if (loggedIn === "true") {
      router.replace("/chat");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex gap-2 items-center">
        <div className="w-2 h-2 rounded-full bg-indigo-400 typing-dot" />
        <div className="w-2 h-2 rounded-full bg-indigo-400 typing-dot" />
        <div className="w-2 h-2 rounded-full bg-indigo-400 typing-dot" />
      </div>
    </div>
  );
}
