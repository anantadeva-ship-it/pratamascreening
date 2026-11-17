import os
import secrets
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

load_dotenv()

app = FastAPI(title="TradingView to Telegram alert relay")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/{hook_secret}")
async def webhook(hook_secret: str, request: Request) -> dict[str, str]:
    expected = os.environ.get("WEBHOOK_SECRET", "")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not expected or not secrets.compare_digest(hook_secret, expected):
        raise HTTPException(status_code=404, detail="Not found")
    if not bot_token or not chat_id:
        raise HTTPException(status_code=503, detail="Telegram environment is not configured")

    try:
        payload: Any = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Expected a JSON alert") from exc
    if not isinstance(payload, dict) or payload.get("source") != "tradingview":
        raise HTTPException(status_code=400, detail="Unexpected payload")

    fields = [
        ("Symbol", payload.get("symbol")),
        ("Timeframe", payload.get("timeframe")),
        ("Side", payload.get("side")),
        ("Setup", payload.get("setup")),
        ("Close", payload.get("price")),
        ("Stop", payload.get("stop")),
        ("Target 1", payload.get("target1")),
        ("Target 2", payload.get("target2")),
        ("Status", "Alert setelah candle tutup; periksa spread dan harga broker."),
    ]
    message = "📊 TradingView intraday alert\n" + "\n".join(
        f"{name}: {value}" for name, value in fields if value is not None
    )

    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            telegram_url,
            json={"chat_id": chat_id, "text": message},
        )
    if response.is_error:
        raise HTTPException(status_code=502, detail="Telegram delivery failed")
    return {"status": "sent"}
