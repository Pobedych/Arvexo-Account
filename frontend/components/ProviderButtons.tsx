"use client";

import { Mail } from "lucide-react";
import { API_URL } from "@/lib/api";
import type { ProviderStatus } from "@/lib/api";

type ProviderButtonsProps = {
  providers: ProviderStatus | null;
};

export function ProviderButtons({ providers }: ProviderButtonsProps) {
  return (
    <div className="provider-list" aria-label="Внешние способы входа">
      <button className="provider-button provider-email" type="button" disabled>
        <Mail size={18} />
        <span>Email</span>
        <small>Форма выше</small>
      </button>

      {/* Google — намеренно отключён */}
      <button className="provider-button" type="button" disabled>
        <span className="provider-letter provider-google">G</span>
        <span>Google</span>
        <small>Скоро</small>
      </button>

      {/* Яндекс */}
      {providers?.yandex ? (
        <a className="provider-button" href={`${API_URL}/auth/yandex`}>
          <span className="provider-letter provider-yandex">Я</span>
          <span>Яндекс</span>
          <small>Войти</small>
        </a>
      ) : (
        <button className="provider-button" type="button" disabled>
          <span className="provider-letter provider-yandex">Я</span>
          <span>Яндекс</span>
          <small>Скоро</small>
        </button>
      )}

      {/* Telegram */}
      {providers?.telegram ? (
        <a className="provider-button" href={`${API_URL}/auth/telegram`}>
          <span>✈</span>
          <span>Telegram</span>
          <small>Войти</small>
        </a>
      ) : (
        <button className="provider-button" type="button" disabled>
          <span>✈</span>
          <span>Telegram</span>
          <small>Скоро</small>
        </button>
      )}
    </div>
  );
}
