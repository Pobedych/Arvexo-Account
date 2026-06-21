"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { refreshAccessToken } from "@/lib/api";

export default function OAuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    refreshAccessToken()
      .then(() => router.replace("/account"))
      .catch(() => router.replace("/login?error=Не удалось завершить вход"));
  }, [router]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
      <p>Выполняем вход…</p>
    </div>
  );
}
