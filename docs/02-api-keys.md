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

You need two values: a **bot token** (identifies your bot) and your **chat id** (identifies you,
so the bot knows where to send messages). They are different things, and the chat id is **not**
in the token or in BotFather's message.

### Step 1: Create your bot and get the token

1. In Telegram, open **@BotFather** and send `/newbot`.
2. Pick a display name, then a username ending in `bot` (e.g. `myjobsearch_bot`).
3. BotFather replies with a link to your bot (`t.me/...`) and a token like
   `123456789:AAF...xyz`.
4. Open `.env` in a text editor and paste it: `TELEGRAM_BOT_TOKEN=123456789:AAF...xyz`

> **Keep the token private.** Anyone with it can control your bot. Never paste it into ChatGPT,
> any AI chat, an email or a screenshot. If it leaks, open @BotFather, send `/revoke`, choose your
> bot, and put the new token in `.env`.
>
> **Common mistake:** the number before the `:` in the token is your **bot's** id, not your chat
> id. Using it as `TELEGRAM_CHAT_ID` causes a 403 error ("bots can't send messages to bots").

### Step 2: Say hi to your bot (required)

Open your bot's link from BotFather (or search for its username), press **Start**, and send
"hi". Telegram does not let a bot message you until you have messaged it first. Skipping this
causes a 403 error ("bot can't initiate conversation with a user").

### Step 3: Find your chat id (pick one way)

**Option A: ask an ID bot (easiest, no code)**

1. In Telegram, search for **@userinfobot** and press **Start**.
2. It replies with your details. Copy the number next to **Id** (e.g. `987654321`).

This is a popular third-party bot. It sees only your public Telegram profile and never your
token.

**Option B: the toolkit command (in a terminal, inside the toolkit folder)**

```bash
python -m job_alert telegram-chat-id
```

It lists the chats that have messaged your bot. Copy the number for your private chat. If it
says no messages were found, go back to Step 2.

This has to run on your own computer. AI chats in the browser (ChatGPT, etc.) cannot run it for
you.

**Option C: your browser (no code)**

Type this into your browser's address bar, replacing `<TOKEN>` with your token:

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Find `"chat":{"id":987654321` and copy the number. If you see `"result":[]`, send your bot
another "hi" and refresh. Do this only in your own browser: the link contains your token, so
don't share it or paste it into an AI chat.

### Step 4: Save and test

1. In `.env`: `TELEGRAM_CHAT_ID=987654321` (your number: digits only, no quotes, no spaces;
   group ids start with `-100`)
2. Test:

```bash
python -m job_alert test-telegram
```

You should receive "✅ Your job alert bot is connected." in Telegram.

### If Telegram says no

`test-telegram` prints Telegram's reason and what to do. The usual ones:

| Error | Cause | Fix |
|---|---|---|
| `403 ... bot can't initiate conversation with a user` | You never messaged the bot | Open the bot, press **Start**, try again |
| `403 ... bots can't send messages to bots` | `TELEGRAM_CHAT_ID` is the bot's own id (the number before `:` in the token) | Get your own id (Step 3) |
| `403 ... bot was blocked by the user` | You blocked or deleted the bot chat | Unblock/restart the bot, send "hi" |
| `403 ... bot is not a member` / `kicked` | Chat id is a group the bot isn't in | Add the bot to the group, or use your private chat id |
| `400 ... chat not found` | Wrong chat id, or a typo | Get your id again (Step 3) |
| `401 Unauthorized` | Wrong or revoked token | Copy the current token from @BotFather (after `/revoke`, only the new one works) |
| `403` with no Telegram reason | A network, firewall, proxy or VPN is blocking `api.telegram.org` | Try another network |

Prefer no phone alerts? Set `notify.channels: [terminal]` in `config.yaml`.

## Your AI

Codex and Claude Code use your own login (`codex login`, or `claude` → `/login`): no key is
stored in this project. API mode needs `LLM_API_KEY` in `.env`; see
[05-choose-your-ai.md](05-choose-your-ai.md).
