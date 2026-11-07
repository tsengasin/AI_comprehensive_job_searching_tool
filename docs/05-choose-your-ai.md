# Choose your AI

The toolkit is not tied to one AI. The skills are plain Markdown files in the open
[Agent Skills](https://agentskills.io) format, and the daily alert can score jobs with three
different engines.

## Which one should I use?

| You have... | Use | Skills (CV, interview) | Daily alert |
|---|---|---|---|
| A ChatGPT plan (Plus/Pro/Business) | **Codex** (CLI, IDE extension or app) | ✅ reads `.agents/skills` | ✅ `engine.type: codex` |
| A Claude plan | **Claude Code** | ✅ reads `.claude/skills` | ✅ `engine.type: claude` |
| An API key from any OpenAI-compatible provider | **API mode** | Use with any agent below | ✅ `engine.type: api` |
| Gemini CLI, Cursor, GitHub Copilot... | That agent | ✅ reads `.agents/skills` / `AGENTS.md` | Use API mode |
| Only ChatGPT in the browser | A **ChatGPT Project** | ✅ see [06-use-in-chatgpt.md](06-use-in-chatgpt.md) | ❌ needs one of the above |

> **Availability differs by place.** Check that your provider officially supports your
> country or territory, and follow its terms. For example, OpenAI and Anthropic each publish a
> list of supported locations, and Hong Kong has not been on them. People in unsupported
> places often use a provider that is available there (for example Azure OpenAI for eligible
> organisations, DeepSeek, Alibaba Cloud Qwen), or a free local model with Ollama.

## Codex (ChatGPT plan)

1. Install Codex: see <https://developers.openai.com/codex> (CLI: `npm install -g @openai/codex`).
2. Sign in: `codex login` (uses your ChatGPT account, no API key).
3. Open the toolkit folder in Codex and say *"Help me set up the job search tool."*
4. In `config.yaml`: `engine.type: codex`

How the daily scorer is locked down: `codex exec` runs in Codex's OS sandbox with
`workspace-write` (it can only write in `data/work/<date>/`), **network turned off**, and
approvals set to `never`, so it cannot escalate.

## Claude Code (Claude plan)

1. Install: <https://claude.com/claude-code>, then run `claude` and `/login`.
2. In `config.yaml`: `engine.type: claude`

The scorer gets only the Read and Write tools: no shell, no web, no MCP servers.

## API mode (most flexible, most locked down)

Python sends your CV, skill profile and the job texts to the model and receives scores back.
The model has **no tools, no files and no internet**. Put the key in `.env` as `LLM_API_KEY`,
then set `config.yaml`:

| Provider | `base_url` | `model` (example) | Notes |
|---|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4.1-mini` | Paid API, separate from ChatGPT plans |
| Azure OpenAI | `https://<your-resource>.openai.azure.com/openai/v1` | your deployment name | Set `key_header: api-key` |
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` | Low cost |
| Qwen (Alibaba Cloud, international) | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | |
| OpenRouter | `https://openrouter.ai/api/v1` | many | One key, many models |
| Ollama (on your computer) | `http://localhost:11434/v1` | `llama3.1`, `qwen2.5` | Free, nothing leaves your computer. `LLM_API_KEY=ollama` |

Model names change often; check your provider's current list. Smaller local models score less
reliably: compare a few results by hand in the first week.

## Privacy: where does my CV go?

Whichever engine you choose, your CV, skill profile and job texts are sent to **that AI
provider** for scoring, under its privacy policy and in its jurisdiction. They are never sent to
the author of this toolkit. If you want nothing to leave your computer, use Ollama.
