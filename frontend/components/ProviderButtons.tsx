"use client";

import { Mail, Send } from "lucide-react";
import type { ProviderStatus } from "@/lib/api";

type ProviderButtonsProps = {
  providers: ProviderStatus | null;
};

export function ProviderButtons({ providers }: ProviderButtonsProps) {
  const rows = [
    { key: "google", label: "Google", icon: <span className="provider-letter provider-google">G</span>, enabled: Boolean(providers?.google) },
    { key: "yandex", label: "Яндекс", icon: <span className="provider-letter provider-yandex">Я</span>, enabled: Boolean(providers?.yandex) },
    { key: "telegram", label: "Telegram", icon: <Send size={18} />, enabled: Boolean(providers?.telegram) }
  ];

  return (
    <div className="provider-list" aria-label="Внешние способы входа">
      <button className="provider-button provider-email" type="button" disabled>
        <Mail size={18} />
        <span>Email</span>
        <small>Форма выше</small>
      </button>
      {rows.map((provider) => (
        <button className="provider-button" type="button" disabled={!provider.enabled} key={provider.key}>
          {provider.icon}
          <span>{provider.label}</span>
          <small>{provider.enabled ? "Доступно" : "Скоро"}</small>
        </button>
      ))}
    </div>
  );
}
