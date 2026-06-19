"use client";

import { Laptop, LogOut, Shield, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

export function AccountDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<AccountUser | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const token = await refreshAccessToken();
        const profile = await apiRequest<AccountUser>("/auth/me", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(profile);
      } catch {
        router.push("/login");
      }
    }
    load();
  }, [router]);

  async function logout() {
    setError("");
    try {
      await apiRequest<{ ok: boolean }>("/auth/logout", { method: "POST" });
      setAccessToken(null);
      router.push("/login");
    } catch (logoutError) {
      setError(logoutError instanceof Error ? logoutError.message : "Не удалось выйти.");
    }
  }

  if (!user) {
    return (
      <main className="account-page">
        <div className="loading-card">Загрузка аккаунта...</div>
      </main>
    );
  }

  const createdAt = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(new Date(user.created_at));

  return (
    <main className="account-page">
      <aside className="account-sidebar">
        <img src="/images/arvexo-mark.png" alt="Arvexo" className="sidebar-mark" />
        <nav>
          <a className="active" href="/account">
            <UserRound size={16} /> Профиль
          </a>
          <a aria-disabled="true">
            <Shield size={16} /> Безопасность
          </a>
          <a aria-disabled="true">
            <Laptop size={16} /> Сессии
          </a>
        </nav>
        <button className="ghost-button" type="button" onClick={logout}>
          <LogOut size={16} /> Выйти
        </button>
      </aside>
      <div className="account-content">
        <div className="account-header">
          <div>
            <p className="section-label">Arvexo Account</p>
            <h1>Профиль</h1>
          </div>
          <button className="secondary-button" type="button" disabled>
            Изменить
          </button>
        </div>
        {error && <p className="auth-error">{error}</p>}
        <div className="profile-panel">
          <div className="avatar">{(user.name || user.email || "A").slice(0, 1).toUpperCase()}</div>
          <div>
            <h2>{user.name || "Пользователь Arvexo"}</h2>
            <p>{user.email || "Email не указан"}</p>
            <small>Создан: {createdAt}</small>
          </div>
        </div>
        <div className="dashboard-grid">
          <article className="account-card">
            <Shield size={20} />
            <h3>Безопасность</h3>
            <p>Управление способами входа будет расширено в следующем релизе.</p>
          </article>
          <article className="account-card">
            <UserRound size={20} />
            <h3>Способы входа</h3>
            <div className="provider-chips">
              {user.connected_providers.map((provider) => (
                <span key={provider}>{provider}</span>
              ))}
            </div>
          </article>
          <article className="account-card">
            <Laptop size={20} />
            <h3>Активные сессии</h3>
            <p>Текущая сессия хранится в httpOnly cookie. Управление войдёт в следующий релиз.</p>
          </article>
        </div>
      </div>
    </main>
  );
}
