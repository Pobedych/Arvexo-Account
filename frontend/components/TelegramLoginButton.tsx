"use client";

import { useEffect, useRef } from "react";
import { API_URL, setAccessToken } from "@/lib/api";
import type { AuthResponse } from "@/lib/api";

type Props = {
  botUsername: string;
  onSuccess?: () => void;
  onError?: (msg: string) => void;
  size?: "large" | "medium" | "small";
  label?: string;
};

declare global {
  interface Window {
    onTelegramAuth?: (user: Record<string, string>) => void;
  }
}

export function TelegramLoginButton({ botUsername, onSuccess, onError, size = "medium", label }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    window.onTelegramAuth = async (tgData) => {
      try {
        const res = await fetch(`${API_URL}/auth/telegram`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(tgData),
          credentials: "include",
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          onError?.(body?.error?.message ?? "Ошибка авторизации через Telegram");
          return;
        }
        const data: AuthResponse = await res.json();
        setAccessToken(data.access_token);
        onSuccess?.();
      } catch {
        onError?.("Не удалось войти через Telegram");
      }
    };

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", size);
    if (label) script.setAttribute("data-userpic", "false");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    script.async = true;
    container.innerHTML = "";
    container.appendChild(script);

    return () => {
      container.innerHTML = "";
      delete window.onTelegramAuth;
    };
  }, [botUsername, size, label, onSuccess, onError]);

  return <div ref={containerRef} />;
}
