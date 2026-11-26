"""Razorpay Subscriptions client (INR). Kept tiny and injectable so tests never call the network."""
from __future__ import annotations

import httpx

from .config import settings

BASE = "https://api.razorpay.com/v1"


class RazorpayClient:
    def _auth(self) -> tuple[str, str]:
        return (settings.razorpay_key_id, settings.razorpay_key_secret)

    def create_subscription(self, plan_id: str, org_id: str, email: str, total_count: int = 120) -> dict:
        r = httpx.post(f"{BASE}/subscriptions", auth=self._auth(), timeout=20, json={
            "plan_id": plan_id, "total_count": total_count, "customer_notify": 1, "notes": {"org_id": org_id, "email": email}})
        r.raise_for_status()
        d = r.json()
        return {"id": d["id"], "short_url": d.get("short_url")}

    def cancel_subscription(self, subscription_id: str, at_cycle_end: bool = True) -> None:
        r = httpx.post(f"{BASE}/subscriptions/{subscription_id}/cancel", auth=self._auth(), timeout=20,
                       json={"cancel_at_cycle_end": 1 if at_cycle_end else 0})
        r.raise_for_status()


def get_client() -> RazorpayClient:
    return RazorpayClient()
