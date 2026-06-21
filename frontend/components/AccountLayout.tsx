"use client";

import { Laptop, LogOut, Shield, UserRound } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { apiRequest, refreshAccessToken, setAccessToken } from "@/lib/api";

const NAV = [
  { href: "/account", icon: <UserRound size={16} />, label: "Профиль" },
  { href: "/security", icon: <Shield size={16} />, label: "Безопасность" },
  { href: "/sessions", icon: <Laptop size={16} />, label: "Сессии" },
];

export function AccountLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  async function logout() {
    try {
      const token = await refreshAccessToken();
      await apiRequest<{ ok: boolean }>("/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      setAccessToken(null);
    } catch {
      // cookie already cleared server-side or expired
    }
    router.push("/login");
  }

  return (
    <main className="account-page">
      <aside className="account-sidebar">
        <img src="/images/arvexo-mark.png" alt="Arvexo" className="sidebar-mark" />
        <nav>
          {NAV.map(({ href, icon, label }) => (
            <a key={href} href={href} className={pathname === href ? "active" : ""}>
              {icon} {label}
            </a>
          ))}
        </nav>
        <button className="ghost-button" type="button" onClick={logout}>
          <LogOut size={16} /> Выйти
        </button>
      </aside>
      <div className="account-content">{children}</div>
    </main>
  );
}
