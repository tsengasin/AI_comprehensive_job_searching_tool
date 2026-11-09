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
3. Open your new bot in Telegram (search for its username) and press **Start**, or send it any
   message such as "hi". **This step is required:** Telegram does not let a bot message you
   until you have messaged it first.
4. Find your chat id:

```bash
python -m job_alert telegram-chat-id
```

   It lists the chats that messaged your bot. Copy **your** number (a private chat; groups start
   with `-100`).
5. In `.env`: `TELEGRAM_CHAT_ID=123456789` (digits only, no quotes, no spaces)
6. Test: `python -m job_alert test-telegram`

### If Telegram says no

`test-telegram` prints Telegram's reason and what to do. The usual ones:

| Error | Cause | Fix |
|---|---|---|
| `403 ... bot can't initiate conversation with a user` | You never messaged the bot | Open the bot, press **Start**, try again |
| `403 ... bots can't send messages to bots` | `TELEGRAM_CHAT_ID` is the bot's own id (the number before `:` in the token) | Run `telegram-chat-id` and use your own id |
| `403 ... bot was blocked by the user` | You blocked or deleted the bot chat | Unblock/restart the bot, send "hi" |
| `403 ... bot is not a member` / `kicked` | Chat id is a group the bot isn't in | Add the bot to the group, or use your private chat id |
| `400 ... chat not found` | Wrong chat id, or a typo | Run `telegram-chat-id` again |
| `401 Unauthorized` | Wrong or revoked token | Copy the token again from @BotFather |
| `403` with no Telegram reason | A network, firewall, proxy or VPN is blocking `api.telegram.org` | Try another network |

Prefer no phone alerts? Set `notify.channels: [terminal]` in `config.yaml`.

## Your AI

Codex and Claude Code use your own login (`codex login`, or `claude` → `/login`): no key is
stored in this project. API mode needs `LLM_API_KEY` in `.env`; see
[05-choose-your-ai.md](05-choose-your-ai.md).
