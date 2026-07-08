**Read [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) first.** It has full project state, live URLs, open threads, secrets/CLI-login inventory, and the migration checklist.

# Mikael Chew Website

Personal brand and book-launch site for Mikael Chew at mikaelchew.com. Static HTML/CSS/JS, hosted on **GitHub Pages** (not Vercel/Netlify — no build step in CI, `build_zh.py` is run manually/locally).

@AGENTS.md

## Standing rules for this project

- **No secrets in files.** This project currently has zero `.env` files by design — the only external secret (Telegram bot token + Sheet endpoint) lives inside Google Apps Script (cloud-side), never in the repo. Keep it that way.
- **Run `/usr/bin/python3 build_zh.py`** (system Python), not the Homebrew `python3` — `lxml` is only installed for system Python on this machine. See gotchas in PROJECT_HANDOFF.md.
- **After editing any EN page with a Chinese equivalent, regenerate `zh/`** via `build_zh.py` before considering the change done.
- **Don't touch `scorecard-setup/apps-script.gs` deployment or Telegram bot config** without confirming with Mikael — it's a live cloud deployment outside this repo, changes there aren't visible in git history.
- **`.claude/` is gitignored** (settings, launch config, auto-commit hook) — it does not travel with `git clone` or `git pull`. Treat it as machine-local state; see PROJECT_HANDOFF.md migration checklist before assuming it exists on a new machine.
- Standing global rules (ask before expensive multi-agent operations, Karpathy coding principles) are inherited from `~/.claude/CLAUDE.md` and `Desktop/CLAUDE.md` — not repeated here.

## Key paths

| What | Path |
|---|---|
| Canonical state doc | [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) |
| Tech stack / conventions / campaign detail | [AGENTS.md](AGENTS.md) |
| Local dev server | `server.py` (gitignored, already present) via `.claude/launch.json` → `python3 server.py` on port 8080 |
| Chinese page generator | `build_zh.py` — regenerates `zh/` from EN pages |
| Brand voice source of truth | `MARBLISM_INSTRUCTIONS.md` |
