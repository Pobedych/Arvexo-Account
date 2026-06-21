"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

type ClientInfo = { client_id: string; name: string };

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
          apiRequest<AccountUser>("/auth/me", {
            headers: { Authorization: `Bearer ${token}` },
          }),
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
      <main className="auth-page">
        <div className="auth-panel" style={{ gridColumn: "1 / -1" }}>
          <div className="auth-form">
            <p className="auth-error">{error}</p>
            <a href="/account" className="ghost-button">← На главную</a>
          </div>
        </div>
      </main>
    );
  }

  if (!user || !clientInfo) {
    return (
      <main className="auth-page">
        <div className="auth-panel" style={{ gridColumn: "1 / -1" }}>
          <div className="loading-card">Загрузка...</div>
        </div>
      </main>
    );
  }

  return (
    <main className="auth-page">
      <div className="auth-hero">
        <div className="auth-hero-logo">
          <img src="/images/arvexo-mark.png" alt="Arvexo" />
          <span className="auth-hero-logo-word">Arvexo Account</span>
        </div>
        <div className="auth-hero-body">
          <h1>Единый <em>вход</em></h1>
          <p>Войдите один раз — используйте все сервисы Arvexo.</p>
        </div>
        <div className="auth-signal-list">
          <span>SSO</span>
          <span>Secure</span>
          <span>One Account</span>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-form">
          <div className="sso-consent">
            <div className="sso-service-badge">{clientInfo.name}</div>
            <h2>Подтвердите вход</h2>
            <p>
              Вы входите в <strong>{clientInfo.name}</strong> через Arvexo Account.
            </p>

            <div className="sso-user-row">
              <div className="sso-avatar">{(user.name || user.email || "A").slice(0, 1).toUpperCase()}</div>
              <div>
                <div className="sso-user-name">{user.name || "Пользователь Arvexo"}</div>
                <div className="sso-user-email">{user.email}</div>
              </div>
            </div>

            {error && <p className="auth-error">{error}</p>}

            <button
              className="primary-button"
              type="button"
              onClick={confirm}
              disabled={loading}
            >
              {loading ? "Перенаправляем..." : `Продолжить в ${clientInfo.name}`}
            </button>

            <button
              className="ghost-button sso-switch"
              type="button"
              onClick={switchAccount}
            >
              Сменить аккаунт
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function SSOContinuePage() {
  return (
    <Suspense fallback={<div className="loading-card">Загрузка...</div>}>
      <SSOContinueContent />
    </Suspense>
  );
}
