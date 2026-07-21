"""Broker data adapter boundary.

This module deliberately exposes a stub until a real broker provider is
configured. It gives the web layer a single place to check whether charts may
use broker-sourced data, without treating public market data as broker data.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerStatus:
    enabled: bool
    connected: bool
    provider: str
    message: str


class BrokerAdapter:
    """Read-only broker adapter facade.

    A real provider should implement quote/history methods behind this class.
    Until then, the application returns an explicit not-connected status.
    """

    def __init__(self, provider: str = "stub", api_url: str = "", api_key: str = "", enabled: bool = False):
        self.provider = (provider or "stub").strip()
        self.api_url = (api_url or "").strip()
        self.api_key = (api_key or "").strip()
        self.enabled = bool(enabled)

    @classmethod
    def from_env(cls) -> "BrokerAdapter":
        return cls(
            provider=os.getenv("BROKER_PROVIDER") or os.getenv("BROKER_API_NAME") or "stub",
            api_url=os.getenv("BROKER_API_URL", ""),
            api_key=os.getenv("BROKER_API_KEY", ""),
            enabled=os.getenv("BROKER_ENABLED", "").lower() in {"1", "true", "yes", "on"},
        )

    @classmethod
    def from_config(cls, config: dict | None = None) -> "BrokerAdapter":
        config = config or {}
        return cls(
            provider=os.getenv("BROKER_PROVIDER") or os.getenv("BROKER_API_NAME") or str(config.get("provider") or "stub"),
            api_url=os.getenv("BROKER_API_URL") or str(config.get("api_url") or ""),
            api_key=os.getenv("BROKER_API_KEY") or str(config.get("api_key") or ""),
            enabled=(os.getenv("BROKER_ENABLED", "").lower() in {"1", "true", "yes", "on"}) or bool(config.get("enabled")),
        )

    @property
    def ready(self) -> bool:
        return self.enabled and self.provider != "stub" and bool(self.api_url and self.api_key)

    @property
    def label(self) -> str:
        return "券商 API" if self.provider == "stub" else self.provider

    def status(self) -> BrokerStatus:
        if self.ready:
            return BrokerStatus(
                enabled=True,
                connected=True,
                provider=self.provider,
                message=f"{self.label} 已配置，可接入券商行情。",
            )
        return BrokerStatus(
            enabled=False,
            connected=False,
            provider=self.provider,
            message="券商 API 未配置，当前不会展示券商行情图。",
        )

    def history(self, symbol: str, market: str, period: str = "1y") -> list[dict]:
        if not self.ready:
            raise RuntimeError("券商 API 未配置，无法获取券商历史行情。")
        raise NotImplementedError("当前券商适配器尚未实现历史行情读取。")
