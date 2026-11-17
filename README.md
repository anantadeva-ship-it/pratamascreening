# TradingView → Telegram intraday alerts

Starter kit for alerts only. It does not place or manage broker orders. Pine indicator signals are designed for a 5-minute chart, filtered by the 15-minute EMA, VWAP, relative volume, volatility, and a recent-bar stop structure. Short alerts are disabled by default. Configure the session input for the exchange and asset you are charting.

## Files

- `alert.pine`: Pine Script v6 indicator. Add it to TradingView Pine Editor, save, and add it to a 5-minute chart.
- `relay.py`: HTTPS webhook receiver that forwards accepted JSON alerts to Telegram.
- `worker.js` and `wrangler.toml`: Cloudflare Workers version of the webhook relay (recommended free hosting option).
- `.env.example`: required environment variables; copy it to `.env` locally and fill in your own values. Never commit `.env`.

## Recommended free hosting: Cloudflare Workers

The Cloudflare Worker accepts a TradingView webhook and sends the Telegram request in the background so it can acknowledge TradingView promptly. The Workers Free plan currently includes up to 100,000 requests per day. The free tier and limits can change; check Cloudflare's current pricing before relying on it for critical alerts.

1. Upload this folder to a GitHub repository. Do not commit a filled-in `.env` file or any tokens.
2. In Cloudflare, create a Worker using **Workers Builds** and connect the GitHub repository. Set the root directory to `outputs/tradingview-telegram-bot` if that is where this folder lives in your repository. The `wrangler.toml` file configures the entry point.
3. In the Worker settings, add these as secrets/environment variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `WEBHOOK_SECRET`.
4. Deploy and check `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/health` for `{"status":"ok"}`.
5. In TradingView's alert webhook URL, use `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/webhook/YOUR_WEBHOOK_SECRET`.

Cloudflare's GitHub integration can deploy a Worker when you push changes. Cloudflare Workers is not a Python host, so deploy `worker.js` there; `relay.py` is for Python application hosts.

## Setup

1. Create a Telegram bot with `@BotFather`, then send it a message from the destination account or group. Obtain the bot token and chat ID using your preferred secure method.
2. Deploy `relay.py` on a public HTTPS host. Set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and a long random `WEBHOOK_SECRET` as host secrets. Install `requirements.txt` and run `uvicorn relay:app --host 0.0.0.0 --port 8000` behind the host's HTTPS proxy.
3. Verify the public `/health` endpoint returns `{"status":"ok"}`.
4. In TradingView, create an alert for the indicator and select **Any alert() function call**. Set the webhook URL to `https://YOUR-HOST/webhook/YOUR_WEBHOOK_SECRET`. The Pine script sends JSON in the alert body.
5. Start with one liquid symbol and paper review. Check the feed/source on the chart and compare every alert with your broker's live price, spread, and liquidity. Close positions before the same session ends; the alert script does not force-close positions.

TradingView webhook alerts require an eligible account/configuration and two-factor authentication. TradingView requires a reachable HTTPS endpoint and may reject slow endpoints, so the relay responds only after Telegram accepts the message. Never put the Telegram bot token in the TradingView alert URL or Pine script. The webhook path secret is still sensitive: keep the alert private and rotate it if exposed.

## Signal limits

The indicator can alert on a confirmed 5-minute candle close. It cannot verify your broker's spread, account short permissions, transaction costs, exchange suspensions, breaking news, or whether the chart feed is real-time. Treat each alert as a conditional screening prompt, not a recommendation or guaranteed execution price. Any targets are calculated from the structure stop and do not include costs.
