function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ status: "ok" });
    }

    if (request.method !== "POST" || url.pathname !== `/webhook/${env.WEBHOOK_SECRET}`) {
      return json({ error: "not found" }, 404);
    }

    if (!env.WEBHOOK_SECRET || !env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_CHAT_ID) {
      return json({ error: "service is not configured" }, 503);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return json({ error: "expected JSON" }, 400);
    }
    if (!payload || typeof payload !== "object" || payload.source !== "tradingview") {
      return json({ error: "unexpected payload" }, 400);
    }

    const fields = [
      ["Symbol", payload.symbol],
      ["Timeframe", payload.timeframe],
      ["Side", payload.side],
      ["Setup", payload.setup],
      ["Close", payload.price],
      ["Stop", payload.stop],
      ["Target 1", payload.target1],
      ["Target 2", payload.target2],
      ["Status", "Alert setelah candle tutup; periksa spread dan harga broker."],
    ];
    const message = "📊 TradingView intraday alert\n" + fields
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([name, value]) => `${name}: ${value}`)
      .join("\n");

    // Acknowledge TradingView promptly; deliver to Telegram in the background.
    ctx.waitUntil((async () => {
      const response = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text: message }),
      });
      if (!response.ok) console.error("Telegram delivery failed", response.status);
    })());

    return json({ status: "accepted" }, 202);
  },
};
