"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { AccountLayout } from "@/components/AccountLayout";
import { API_URL, apiRequest, refreshAccessToken, setAccessToken, type Identity, type ProviderStatus } from "@/lib/api";

const PROVIDER_LABELS: Record<string, string> = {
  email: "Email / пароль",
  yandex: "Яндекс",
  telegram: "Telegram",
  google: "Google",
};

function SecurityPageInner() {
  const router = useRouter();
  const params = useSearchParams();
  const [identities, setIdentities] = useState<Identity[] | null>(null);
  const [providers, setProviders] = useState<ProviderStatus | null>(null);
  const [hasPassword, setHasPassword] = useState(false);
  const [error, setError] = useState(params.get("error") ?? "");
  const [success, setSuccess] = useState(params.get("connected") ? `${params.get("connected")} успешно подключён` : "");
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  const [currentPwd, setCurrentPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);

  useEffect(() => {
    async function load() {
      let token: string;
      try {
        token = await refreshAccessToken();
        setAccessToken(token);
      } catch (e) {
        // Нет сессии — редирект на логин
        router.push("/login");
        return;
      }
      try {
        const [data, prov] = await Promise.all([
          apiRequest<Identity[]>("/account/identities", { headers: { Authorization: `Bearer ${token}` } }),
          apiRequest<ProviderStatus>("/auth/providers"),
        ]);
        setIdentities(data);
        setProviders(prov);
        setHasPassword(data.some((i) => i.provider === "email"));
      } catch (e) {
        // Показываем ошибку вместо редиректа
        setError(e instanceof Error ? e.message : "Ошибка загрузки данных");
        setIdentities([]);
      }
    }
    load();
  }, [router]);

  async function disconnect(provider: string) {
    setError("");
    setDisconnecting(provider);
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>(`/account/identities/${provider}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setIdentities((prev) => prev?.filter((i) => i.provider !== provider) ?? null);
      setSuccess("Способ входа отвязан.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setDisconnecting(null);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setPwdLoading(true);
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>("/account/password", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password: currentPwd, new_password: newPwd }),
      });
      setSuccess("Пароль успешно изменён.");
      setCurrentPwd("");
      setNewPwd("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setPwdLoading(false);
    }
  }

  if (!identities) {
    return (
      <main className="account-page">
        <div className="loading-card">Загрузка...</div>
      </main>
    );
  }

  return (
    <AccountLayout>
      <div className="account-header">
        <div>
          <p className="section-label">Arvexo Account</p>
          <h1>Безопасность</h1>
        </div>
      </div>

      {error && <p className="auth-error">{error}</p>}
      {success && <p className="auth-success">{success}</p>}

      {hasPassword && (
        <section className="settings-section">
          <h2 className="settings-section-title">Сменить пароль</h2>
          <form className="settings-form" onSubmit={changePassword}>
            <label>
              Текущий пароль
              <input
                type="password"
                value={currentPwd}
                onChange={(e) => setCurrentPwd(e.target.value)}
                required
                autoComplete="current-password"
              />
            </label>
            <label>
              Новый пароль
              <input
                type="password"
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>
            <button className="primary-button settings-submit" type="submit" disabled={pwdLoading}>
              {pwdLoading ? "Сохраняем..." : "Сменить пароль"}
            </button>
          </form>
        </section>
      )}

      {/* Connect new providers */}
      {providers && (
        <section className="settings-section">
          <h2 className="settings-section-title">Подключить способ входа</h2>
          <div className="connect-providers">
            {providers.yandex && !identities?.some((i) => i.provider === "yandex") && (
              <a className="provider-button" href={`${API_URL}/auth/yandex/connect`}>
                <span className="provider-letter provider-yandex">Я</span>
                <span>Подключить Яндекс</span>
              </a>
            )}
            {providers.telegram && !identities?.some((i) => i.provider === "telegram") && (
              <a className="provider-button" href={`${API_URL}/auth/telegram/connect`}>
                <span>✈</span>
                <span>Подключить Telegram</span>
              </a>
            )}
          </div>
        </section>
      )}

      <section className="settings-section">
        <h2 className="settings-section-title">Подключённые способы входа</h2>
        <div className="identities-list">
          {identities.map((identity) => {
            const canDisconnect = identities.length > 1;
            const added = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(
              new Date(identity.created_at)
            );
            return (
              <div key={identity.provider} className="identity-row">
                <div>
                  <span className="identity-provider">{PROVIDER_LABELS[identity.provider] ?? identity.provider}</span>
                  {identity.provider_email && (
                    <span className="identity-email">{identity.provider_email}</span>
                  )}
                  <span className="identity-date">Добавлен: {added}</span>
                </div>
                <button
                  className="danger-button"
                  type="button"
                  disabled={!canDisconnect || disconnecting === identity.provider}
                  onClick={() => disconnect(identity.provider)}
                  title={canDisconnect ? "Отвязать" : "Нельзя отвязать последний способ входа"}
                >
                  {disconnecting === identity.provider ? "..." : "Отвязать"}
                </button>
              </div>
            );
          })}
        </div>
      </section>
    </AccountLayout>
  );
}

export default function SecurityPage() {
  return (
    <Suspense>
      <SecurityPageInner />
    </Suspense>
  );
}
