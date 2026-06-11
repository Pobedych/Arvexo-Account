"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiRequest, type AuthResponse, type ProviderStatus, setAccessToken } from "@/lib/api";
import { ProviderButtons } from "@/components/ProviderButtons";

type AuthFormProps = {
  mode: "login" | "register";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState<ProviderStatus | null>(null);

  useEffect(() => {
    apiRequest<ProviderStatus>("/auth/providers")
      .then(setProviders)
      .catch(() => setProviders({ google: false, yandex: false, telegram: false }));
  }, []);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = mode === "register" ? { email, password, name } : { email, password };
      const data = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setAccessToken(data.access_token);
      router.push("/account");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось выполнить запрос.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <div className="auth-tabs">
        <Link className={mode === "login" ? "active" : ""} href="/login">
          Вход
        </Link>
        <Link className={mode === "register" ? "active" : ""} href="/register">
          Регистрация
        </Link>
      </div>
      <div className="form-copy">
        <h2>{mode === "login" ? "Войдите, чтобы продолжить" : "Регистрация"}</h2>
        <p>Управляйте профилем и активными сессиями Arvexo Account.</p>
      </div>
      {mode === "register" && (
        <label>
          Имя
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={120} placeholder="Alexey" autoComplete="given-name" />
        </label>
      )}
      <label>
        Email
        <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="name@arvexo.com" autoComplete="email" required />
      </label>
      <label>
        Пароль
        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          type="password"
          minLength={mode === "register" ? 8 : 1}
          placeholder="••••••••••••"
          autoComplete={mode === "register" ? "new-password" : "current-password"}
          required
        />
      </label>
      {error && <p className="auth-error">{error}</p>}
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? "Подождите..." : mode === "login" ? "Войти" : "Создать аккаунт"}
      </button>
      <div className="divider">
        <span>или продолжить через</span>
      </div>
      <ProviderButtons providers={providers} />
    </form>
  );
}
