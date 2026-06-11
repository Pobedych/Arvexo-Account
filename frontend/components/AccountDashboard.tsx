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
        <section className="account-card loading-card">Загрузка аккаунта...</section>
      </main>
    );
  }

  const createdAt = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(new Date(user.created_at));

  return (
    <main className="account-page">
      <section className="account-sidebar">
        <img src="/images/arvexo-mark.png" alt="" className="sidebar-mark" />
        <nav>
          <a className="active" href="/account">
            <UserRound size={18} /> Профиль
          </a>
          <a aria-disabled="true">
            <Shield size={18} /> Безопасность
          </a>
          <a aria-disabled="true">
            <Laptop size={18} /> Активные сессии
          </a>
        </nav>
        <button className="ghost-button" type="button" onClick={logout}>
          <LogOut size={18} /> Выйти
        </button>
      </section>
      <section className="account-content">
        <div className="account-header">
          <div>
            <p className="section-label">Arvexo Account</p>
            <h1>Профиль</h1>
          </div>
          <button className="secondary-button" type="button" disabled>
            Изменить профиль
          </button>
        </div>
        {error && <p className="auth-error">{error}</p>}
        <div className="profile-panel">
          <div className="avatar">{(user.name || user.email || "A").slice(0, 1).toUpperCase()}</div>
          <div>
            <h2>{user.name || "Пользователь Arvexo"}</h2>
            <p>{user.email || "Email не указан"}</p>
            <small>Аккаунт создан: {createdAt}</small>
          </div>
        </div>
        <div className="dashboard-grid">
          <article className="account-card">
            <Shield size={24} />
            <h3>Безопасность</h3>
            <p>Управление способами входа будет расширено в следующем срезе.</p>
          </article>
          <article className="account-card">
            <UserRound size={24} />
            <h3>Подключённые способы входа</h3>
            <div className="provider-chips">
              {user.connected_providers.map((provider) => (
                <span key={provider}>{provider}</span>
              ))}
            </div>
          </article>
          <article className="account-card">
            <Laptop size={24} />
            <h3>Активные сессии</h3>
            <p>Текущая refresh-сессия хранится в httpOnly cookie. Управление списком сессий входит в Priority 2.</p>
          </article>
        </div>
      </section>
    </main>
  );
}
