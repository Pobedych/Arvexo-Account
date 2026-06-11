import type { ReactNode } from "react";
import { Logo } from "@/components/Logo";

export function AuthShell({ children, mode }: { children: ReactNode; mode: "login" | "register" }) {
  return (
    <main className="auth-page">
      <section className="auth-hero" aria-label="Arvexo Account">
        <Logo />
        <div className="auth-brand-mark" aria-hidden="true">
          <img src="/images/arvexo-mark.png" alt="" />
        </div>
        <h1>{mode === "login" ? "Войдите в Arvexo Account" : "Создайте Arvexo Account"}</h1>
        <p>Единый аккаунт для сервисов Arvexo</p>
        <div className="auth-signal-list">
          <span>httpOnly refresh sessions</span>
          <span>Internal SSO ready</span>
          <span>Arvexo ecosystem</span>
        </div>
      </section>
      <section className="auth-panel">{children}</section>
    </main>
  );
}
