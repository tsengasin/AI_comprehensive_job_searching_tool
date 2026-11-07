# Getting your keys (all free to start)

Every key goes into **your own `.env` file** on your computer. The toolkit author never sees
them, and there is no server in between.

**Golden rules**
- Paste keys only into `.env`. Not into chat, GitHub issues, screenshots or shared documents.
- If a key ever leaks, regenerate it on the provider's site (the old one stops working).
- You only need **one** job source to start. Remove the other from `config.yaml` → `sources`.

## Jooble (job search API)

1. Go to <https://jooble.org/api/about> and request an API key with your email.
2. You receive the key by email.
3. In `.env`: `JOOBLE_APP_KEY=your-key-here`

## SerpApi (Google Jobs results)

1. Sign up at <https://serpapi.com> (the free plan has a monthly search quota).
2. Copy your key from <https://serpapi.com/manage-api-key>.
3. In `.env`: `SERPAPI_KEY=your-key-here`

Each query in `config.yaml` uses one search per day. 5 queries × 30 days = 150 searches a month,
so check your plan's quota and keep the query list short.

## Telegram (daily digest on your phone)

1. In Telegram, open **@BotFather**, send `/newbot`, pick a name. It gives you a token like
   `123456789:AA...`.
2. In `.env`: `TELEGRAM_BOT_TOKEN=that-token`
3. Open your new bot in Telegram and send it any message (e.g. "hi").
4. Find your chat id: open this in a browser, replacing `<TOKEN>` with your token:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Look for `"chat":{"id":123456789` and copy the number. (Do this yourself; do not ask an AI
   agent to open the link, since it contains your token.)
5. In `.env`: `TELEGRAM_CHAT_ID=123456789`
6. Test: `python -m job_alert test-telegram`

Prefer no phone alerts? Set `notify.channels: [terminal]` in `config.yaml`.

## Claude Code

The daily scoring uses your own Claude Code login (`claude` → `/login`). No Anthropic API key is
stored in this project.
