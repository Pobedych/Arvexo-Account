"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AccountLayout } from "@/components/AccountLayout";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

export default function DeleteAccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<AccountUser | null>(null);
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const token = await refreshAccessToken();
        setAccessToken(token);
        const data = await apiRequest<AccountUser>("/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(data);
      } catch {
        router.push("/login");
      }
    }
    load();
  }, [router]);

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    if (confirm !== user.email) {
      setError("Email не совпадает. Введите ваш email для подтверждения.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>("/auth/me", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setAccessToken(null);
      router.push("/login");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
      setLoading(false);
    }
  }

  if (!user) {
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
          <h1>Удалить аккаунт</h1>
        </div>
      </div>

      <div className="danger-warning">
        <h2>Это действие необратимо</h2>
        <p>
          После удаления аккаунта все ваши данные будут безвозвратно удалены: профиль, способы входа,
          активные сессии. Восстановить аккаунт будет невозможно.
        </p>
      </div>

      <form className="settings-form settings-form--narrow" onSubmit={handleDelete}>
        {error && <p className="auth-error">{error}</p>}
        <label>
          Введите ваш email <strong>{user.email}</strong> для подтверждения
          <input
            type="email"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder={user.email ?? ""}
            required
            autoComplete="off"
          />
        </label>
        <button
          className="primary-button danger-primary-button"
          type="submit"
          disabled={loading || confirm !== user.email}
        >
          {loading ? "Удаляем аккаунт..." : "Удалить аккаунт навсегда"}
        </button>
        <a href="/account" className="cancel-link">Отмена</a>
      </form>
    </AccountLayout>
  );
}
