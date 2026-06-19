import type { ReactNode } from "react";

export function AuthShell({ children, mode }: { children: ReactNode; mode: "login" | "register" }) {
  return (
    <main className="auth-page">
      <section className="auth-hero" aria-label="Arvexo Account">
        <div className="auth-hero-logo">
          <img src="/images/arvexo-mark.png" alt="Arvexo" />
          <span className="auth-hero-logo-word">Arvexo</span>
        </div>
        <div className="auth-hero-body">
          <h1>
            {mode === "login" ? (
              <>Войдите в <em>Account</em></>
            ) : (
              <>Создайте <em>Account</em></>
            )}
          </h1>
          <p>Единый аккаунт для всех сервисов экосистемы Arvexo.</p>
        </div>
        <div className="auth-signal-list">
          <span>httpOnly sessions</span>
          <span>SSO ready</span>
          <span>Arvexo ecosystem</span>
        </div>
      </section>
      <section className="auth-panel">{children}</section>
    </main>
  );
}
