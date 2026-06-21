"use client";

import { Laptop, Shield, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AccountLayout } from "@/components/AccountLayout";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

export function AccountDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<AccountUser | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const token = await refreshAccessToken();
        const profile = await apiRequest<AccountUser>("/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setAccessToken(token);
        setUser(profile);
      } catch {
        router.push("/login");
      }
    }
    load();
  }, [router]);

  if (!user) {
    return (
      <main className="account-page">
        <div className="loading-card">Загрузка аккаунта...</div>
      </main>
    );
  }

  const createdAt = new Intl.DateTimeFormat("ru-RU", { dateStyle: "medium" }).format(new Date(user.created_at));

  return (
    <AccountLayout>
      <div className="account-header">
        <div>
          <p className="section-label">Arvexo Account</p>
          <h1>Профиль</h1>
        </div>
      </div>

      <div className="profile-panel">
        <div className="avatar">{(user.name || user.email || "A").slice(0, 1).toUpperCase()}</div>
        <div>
          <h2>{user.name || "Пользователь Arvexo"}</h2>
          <p>{user.email || "Email не указан"}</p>
          <small>Создан: {createdAt}</small>
        </div>
      </div>

      <div className="dashboard-grid">
        <a href="/security" className="account-card account-card-link">
          <Shield size={20} />
          <h3>Безопасность</h3>
          <p>Смена пароля и управление способами входа.</p>
        </a>
        <div className="account-card">
          <UserRound size={20} />
          <h3>Способы входа</h3>
          <div className="provider-chips">
            {user.connected_providers.map((provider) => (
              <span key={provider}>{provider}</span>
            ))}
          </div>
        </div>
        <a href="/sessions" className="account-card account-card-link">
          <Laptop size={20} />
          <h3>Активные сессии</h3>
          <p>Управляйте устройствами, где вы вошли в аккаунт.</p>
        </a>
      </div>

      <div className="danger-zone">
        <h3>Опасная зона</h3>
        <p>Удаление аккаунта необратимо.</p>
        <a href="/delete-account" className="danger-link">Удалить аккаунт →</a>
      </div>
    </AccountLayout>
  );
}
