"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AccountLayout } from "@/components/AccountLayout";
import { apiRequest, refreshAccessToken, setAccessToken, type UserSession } from "@/lib/api";

function formatDate(iso: string) {
  return new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
}

function parseUA(ua: string | null) {
  if (!ua) return "Неизвестное устройство";
  if (/mobile/i.test(ua)) return "Мобильное устройство";
  if (/tablet/i.test(ua)) return "Планшет";
  return "Компьютер";
}

export default function SessionsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<UserSession[] | null>(null);
  const [error, setError] = useState("");
  const [revoking, setRevoking] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);

  async function load() {
    try {
      const token = await refreshAccessToken();
      setAccessToken(token);
      const data = await apiRequest<UserSession[]>("/sessions", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSessions(data);
    } catch {
      router.push("/login");
    }
  }

  useEffect(() => { load(); }, [router]);

  async function revokeOne(id: string) {
    setError("");
    setRevoking(id);
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>(`/sessions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setSessions((prev) => prev?.filter((s) => s.id !== id) ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setRevoking(null);
    }
  }

  async function revokeOthers() {
    setError("");
    setRevokingAll(true);
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ revoked: number }>("/sessions", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setRevokingAll(false);
    }
  }

  if (!sessions) {
    return (
      <main className="account-page">
        <div className="loading-card">Загрузка...</div>
      </main>
    );
  }

  const hasOthers = sessions.some((s) => !s.current);

  return (
    <AccountLayout>
      <div className="account-header">
        <div>
          <p className="section-label">Arvexo Account</p>
          <h1>Активные сессии</h1>
        </div>
        {hasOthers && (
          <button
            className="danger-button"
            type="button"
            onClick={revokeOthers}
            disabled={revokingAll}
          >
            {revokingAll ? "Завершаем..." : "Завершить все остальные"}
          </button>
        )}
      </div>

      {error && <p className="auth-error">{error}</p>}

      {sessions.length === 0 ? (
        <p className="empty-state">Активных сессий нет.</p>
      ) : (
        <div className="sessions-list">
          {sessions.map((s) => (
            <div key={s.id} className={`session-row${s.current ? " session-row--current" : ""}`}>
              <div className="session-info">
                <div className="session-device">
                  {parseUA(s.user_agent)}
                  {s.current && <span className="session-badge">Текущая</span>}
                </div>
                {s.user_agent && <div className="session-ua">{s.user_agent}</div>}
                <div className="session-meta">
                  {s.ip_address && <span>IP: {s.ip_address}</span>}
                  <span>Вход: {formatDate(s.created_at)}</span>
                  <span>Истекает: {formatDate(s.expires_at)}</span>
                </div>
              </div>
              {!s.current && (
                <button
                  className="danger-button"
                  type="button"
                  disabled={revoking === s.id}
                  onClick={() => revokeOne(s.id)}
                >
                  {revoking === s.id ? "..." : "Завершить"}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </AccountLayout>
  );
}
