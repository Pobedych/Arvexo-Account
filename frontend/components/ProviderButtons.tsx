"use client";

import { Mail } from "lucide-react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/api";
import type { ProviderStatus } from "@/lib/api";
import { TelegramLoginButton } from "./TelegramLoginButton";

type ProviderButtonsProps = {
  providers: ProviderStatus | null;
};

export function ProviderButtons({ providers }: ProviderButtonsProps) {
  const router = useRouter();

  return (
    <div className="provider-list" aria-label="Внешние способы входа">
      <button className="provider-button provider-email" type="button" disabled>
        <Mail size={18} />
        <span>Email</span>
        <small>Форма выше</small>
      </button>

      {/* Google — intentionally disabled */}
      <button className="provider-button" type="button" disabled key="google">
        <span className="provider-letter provider-google">G</span>
        <span>Google</span>
        <small>Скоро</small>
      </button>

      {/* Yandex */}
      {providers?.yandex ? (
        <a className="provider-button" href={`${API_URL}/auth/yandex`} key="yandex">
          <span className="provider-letter provider-yandex">Я</span>
          <span>Яндекс</span>
          <small>Доступно</small>
        </a>
      ) : (
        <button className="provider-button" type="button" disabled key="yandex">
          <span className="provider-letter provider-yandex">Я</span>
          <span>Яндекс</span>
          <small>Скоро</small>
        </button>
      )}

      {/* Telegram */}
      {providers?.telegram && providers.telegram_bot_username ? (
        <div className="provider-button provider-telegram-wrap" key="telegram">
          <TelegramLoginButton
            botUsername={providers.telegram_bot_username}
            onSuccess={() => router.push("/account")}
          />
        </div>
      ) : (
        <button className="provider-button" type="button" disabled key="telegram">
          <span>✈</span>
          <span>Telegram</span>
          <small>Скоро</small>
        </button>
      )}
    </div>
  );
}
