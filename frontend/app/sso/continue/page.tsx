"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

type ClientInfo = { client_id: string; name: string };

function Avatar({ user }: { user: AccountUser }) {
  const initials = (user.name || user.email || "A").slice(0, 1).toUpperCase();
  if (user.avatar_url) {
    return <img src={user.avatar_url} alt={initials} className="sso-big-avatar-img" />;
  }
  return <div className="sso-big-avatar-letter">{initials}</div>;
}

function SSOContinueContent() {
  const router = useRouter();
  const params = useSearchParams();

  const clientId = params.get("client_id") ?? "";
  const redirectUri = params.get("redirect_uri") ?? "";
  const state = params.get("state") ?? undefined;
  const scope = params.get("scope") ?? undefined;

  const [user, setUser] = useState<AccountUser | null>(null);
  const [clientInfo, setClientInfo] = useState<ClientInfo | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!clientId || !redirectUri) {
      setError("Неверные параметры запроса.");
      return;
    }

    async function load() {
      try {
        const token = await refreshAccessToken();
        setAccessToken(token);
        const [profile, info] = await Promise.all([
          apiRequest<AccountUser>("/auth/me", { headers: { Authorization: `Bearer ${token}` } }),
          apiRequest<ClientInfo>(`/sso/client?client_id=${encodeURIComponent(clientId)}`),
        ]);
        setUser(profile);
        setClientInfo(info);
      } catch {
        const next = `/sso/continue?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}${state ? `&state=${encodeURIComponent(state)}` : ""}`;
        router.push(`/login?next=${encodeURIComponent(next)}`);
      }
    }
    load();
  }, [clientId, redirectUri, state, router]);

  async function confirm() {
    setError("");
    setLoading(true);
    try {
      const token = await refreshAccessToken();
      const result = await apiRequest<{ redirect_url: string }>("/sso/confirm", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ client_id: clientId, redirect_uri: redirectUri, state, scope }),
      });
      window.location.href = result.redirect_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
      setLoading(false);
    }
  }

  async function switchAccount() {
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>("/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setAccessToken(null);
    } catch {
      // ignore
    }
    const next = `/sso/continue?client_id=${encodeURIComponent(clientId)}&redirect_uri=${encodeURIComponent(redirectUri)}${state ? `&state=${encodeURIComponent(state)}` : ""}`;
    router.push(`/login?next=${encodeURIComponent(next)}`);
  }

  if (error && !user) {
    return (
      <div className="sso-page">
        <div className="sso-card">
          <p className="auth-error">{error}</p>
          <a href="/account" className="ghost-button" style={{ justifyContent: "center" }}>← На главную</a>
        </div>
      </div>
    );
  }

  if (!user || !clientInfo) {
    return (
      <div className="sso-page">
        <div className="loading-card">Загрузка...</div>
      </div>
    );
  }

  const displayName = [user.name, user.last_name].filter(Boolean).join(" ") || "Пользователь Arvexo";

  return (
    <div className="sso-page">
      <div className="sso-card">
        {/* Логотип */}
        <div className="sso-logo">
          <img src="/images/arvexo-mark.png" alt="Arvexo" className="sso-logo-mark" />
          <span className="sso-logo-word">Arvexo</span>
        </div>

        {/* Сервис запрашивает вход */}
        <p className="sso-service-line">
          <strong>{clientInfo.name}</strong> запрашивает вход через Arvexo Account
        </p>

        {/* Аватар + имя */}
        <div className="sso-identity">
          <Avatar user={user} />
          <h2 className="sso-identity-name">Войти как {displayName}</h2>
          {user.email && <p className="sso-identity-email">{user.email}</p>}
        </div>

        {error && <p className="auth-error">{error}</p>}

        {/* Кнопки */}
        <button
          className="primary-button"
          type="button"
          onClick={confirm}
          disabled={loading}
        >
          {loading ? "Перенаправляем..." : "Продолжить"}
        </button>

        <button className="sso-switch-btn" type="button" onClick={switchAccount}>
          Использовать другой аккаунт
        </button>
      </div>
    </div>
  );
}

export default function SSOContinuePage() {
  return (
    <Suspense fallback={<div className="loading-card">Загрузка...</div>}>
      <SSOContinueContent />
    </Suspense>
  );
}
