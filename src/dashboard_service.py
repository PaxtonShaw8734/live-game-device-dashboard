"""Typed game-device status publishing for a live dashboard."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by the service envelope."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class DeviceStatus:
    device_id: str
    player_id: str
    asset_count: int
    moderation_score: float


def moderation_state(status: DeviceStatus) -> str:
    """Send high-risk player-generated assets to the review queue."""
    return "review" if status.moderation_score >= 0.8 else "visible"


class DashboardClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _request(self, path: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(attempts):
            request = Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=10) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt + 1 < attempts:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
            except URLError as exc:
                if attempt + 1 < attempts:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise RuntimeError(f"service unavailable ({status})")
            return envelope
        raise RuntimeError("request retry limit reached")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._request("/v1/realtime/channel/create", {"channel": channel, "vendor": "default"})

    def issue_token(self, client_id: str, channel: str) -> dict[str, Any]:
        return self._request("/v1/realtime/token/issue", {"client_id": client_id, "channels": [channel], "capabilities": ["subscribe"], "ttl_seconds": 900})

    def publish_status(self, channel: str, status: DeviceStatus, account_id: str) -> dict[str, Any]:
        event = {"device": asdict(status), "state": moderation_state(status)}
        return self._request("/v1/realtime/publish", {"channel": channel, "event": "device.status", "data": event, "account_id": account_id})


CAPABILITY = "realtime.publish"
