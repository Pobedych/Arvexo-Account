"use client";

import { Globe, Laptop, Lock, Shield, Trash2, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AccountLayout } from "@/components/AccountLayout";
import { apiRequest, refreshAccessToken, setAccessToken, type AccountUser } from "@/lib/api";

function Avatar({ user, size = 80 }: { user: AccountUser; size?: number }) {
  const initials = (user.name || user.email || "A").slice(0, 1).toUpperCase();
  if (user.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt={initials}
        className="account-avatar-img"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <div className="account-avatar-letter" style={{ width: size, height: size, fontSize: size * 0.4 }}>
      {initials}
    </div>
  );
}

const CARDS = [
  {
    href: "/security",
    icon: <Shield size={22} />,
    title: "Безопасность",
    desc: "Пароль и способы входа",
    color: "#4A90D9",
  },
  {
    href: "/sessions",
    icon: <Laptop size={22} />,
    title: "Устройства",
    desc: "Активные сессии и вход",
    color: "#7B61FF",
  },
  {
    href: null,
    icon: <Globe size={22} />,
    title: "Конфиденциальность",
    desc: "Управление данными",
    color: "#1FB46A",
    disabled: true,
  },
  {
    href: null,
    icon: <Lock size={22} />,
    title: "Приватность",
    desc: "Настройки видимости",
    color: "#F5A623",
    disabled: true,
  },
];

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

  const displayName = [user.name, user.last_name].filter(Boolean).join(" ") || "Пользователь Arvexo";

  return (
    <AccountLayout>
      {/* Hero профиля */}
      <div className="account-profile-hero">
        <Avatar user={user} size={96} />
        <h1 className="account-profile-name">{displayName}</h1>
        <p className="account-profile-email">{user.email ?? "Email не указан"}</p>
        <div className="account-profile-providers">
          {user.connected_providers.map((p) => (
            <span key={p} className="provider-chip">{p}</span>
          ))}
        </div>
        <Link href="/security" className="secondary-button account-profile-edit-btn">
          Редактировать аккаунт
        </Link>
      </div>

      {/* Карточки */}
      <div className="google-cards-grid">
        {CARDS.map((card) => {
          const inner = (
            <>
              <div className="google-card-icon" style={{ background: card.color + "18", color: card.color }}>
                {card.icon}
              </div>
              <div>
                <h3 className="google-card-title">{card.title}</h3>
                <p className="google-card-desc">{card.desc}</p>
              </div>
              {card.disabled && <span className="google-card-soon">Скоро</span>}
            </>
          );
          return card.href ? (
            <Link key={card.title} href={card.href} className="google-card">
              {inner}
            </Link>
          ) : (
            <div key={card.title} className="google-card google-card--disabled">
              {inner}
            </div>
          );
        })}
      </div>

      {/* Подключённые провайдеры */}
      <div className="account-connected-section">
        <p className="section-label">Способы входа</p>
        <div className="account-providers-row">
          {user.connected_providers.length === 0 ? (
            <span className="account-providers-empty">Не подключено</span>
          ) : (
            user.connected_providers.map((p) => (
              <div key={p} className="account-provider-item">
                <UserRound size={14} />
                <span>{p}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Опасная зона */}
      <div className="danger-zone">
        <Trash2 size={16} style={{ color: "var(--error)", marginBottom: 8 }} />
        <h3>Удалить аккаунт</h3>
        <p>Удаление аккаунта необратимо и затронет все сервисы Arvexo.</p>
        <a href="/delete-account" className="danger-link">Удалить аккаунт →</a>
      </div>
    </AccountLayout>
  );
}
