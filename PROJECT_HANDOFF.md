# Project Handoff — Mikael Chew Website

Canonical state document for this repo. Read this before doing anything else in a new session or on a new machine. See [CLAUDE.md](CLAUDE.md) for the short entry point and standing rules.

Last updated: 2026-07-08 (documentation pass, no code/deploy changes made).

---

## 1. Business / Context

Personal brand and book-launch hub for Mikael Chew at **mikaelchew.com**. Two jobs at once:

1. **Book launch** — 12-week campaign for 《直銷孫子兵法之不戰而勝》 ("The Art of War for Direct Selling"), target launch window July–August 2026. `book.html` is currently a "Coming Soon" page that upgrades to a live purchase page at launch. Full campaign detail in `BOOK_LAUNCH_PLAN.md`.
2. **Personal brand / field-building funnel** — `work-with-me.html`, `speaking.html`, `about.html`, the blog, and the new `scorecard.html` lead magnet support Mikael's transition from Zinzino Malaysia corporate back into the field as a Zinzino partner/leader under Ignite Ventures. This site is part of that broader personal-brand infrastructure (see `~/Desktop/CLAUDE.md` and the Vault for the full business context — this repo is scoped to the website only).

Brand voice, visual identity (black #1a1a1a / beige #f5f0e8 / red #c0392b), and content pillars are defined in `MARBLISM_INSTRUCTIONS.md` — treat that as the source of truth for anything published.

---

## 2. Live Assets

| Asset | URL | Source in this repo | Hosting | Status |
|---|---|---|---|---|
| Main site | https://www.mikaelchew.com | root, `main` branch | GitHub Pages (`mikaelchew.github.io`) | **LIVE** |
| Apex domain | https://mikaelchew.com | same (CNAME file + DNS A records → GitHub Pages IPs) | same | **LIVE**, redirects to www |
| Chinese mirror | https://www.mikaelchew.com/zh/ | `zh/` — generated, do not hand-edit | same | **LIVE**, regenerate via `build_zh.py` after EN edits |
| Blog (39 posts) | /blog/ | `blog/` | same | **LIVE** |
| Book landing page | /book.html | root | same | **LIVE but "Coming Soon"** — not yet the purchase page |
| Strategic Leader Scorecard | /scorecard.html | root | same | **LIVE page, backend NOT connected** — `ENDPOINT` is empty (`""`), so submissions currently only log to console (demo mode), nothing is captured |
| Scorecard backend (when connected) | Google Sheet + Apps Script Web App | `scorecard-setup/apps-script.gs` (source copy only — the deployed script lives in Google's cloud) | Google Cloud, tied to Mikael's Google account — **not this repo, not this machine** | Per `scorecard-setup/SETUP.md`, appears **not yet deployed** — confirm with Mikael before assuming it's live |
| Chapter 1 preview PDF | /downloads/chapter1-sample.pdf | `downloads/` | same | **LIVE** |
| Research doc (internal, not published) | — | `AI_DS_CHANNEL_FEASIBILITY.md` | n/a — plain repo file, never served | Not a site page |

**Hosting is GitHub Pages, not Vercel/Netlify** — confirmed via DNS (`www` CNAMEs to `mikaelchew.github.io`; apex A records are GitHub Pages' `185.199.108-111.153`) and the absence of any `vercel.json`/`netlify.toml`. No CI build step — GitHub Pages serves directly from the `main` branch root on every push.

---

## 3. Architecture in Brief

- **Pure static HTML/CSS/JS.** No framework, no `package.json`, no `node_modules` — zero npm dependency chain.
- **`build_zh.py`** (Python + `lxml`) generates the Traditional-Chinese `/zh/` mirror by transforming the EN HTML pages. Must be re-run after editing any EN page that has a `zh` equivalent — it is not automatic/CI-driven.
- **`server.py`** — a ~10-line stdlib `http.server` wrapper for local preview on port 8080. Gitignored (recreatable from this doc if ever lost — see file contents in git history or below).
- **Fonts + Font Awesome are self-hosted** under `vendor/` (not CDN-loaded) — a deliberate perf decision, see Decisions Log.
- **No JS framework** — single `js/main.js`.
- **Lead-gen backend pattern**: forms on this site (e.g. Scorecard) POST to a Google Apps Script Web App tied to a Google Sheet, which optionally pings a Telegram bot. This is the *same pattern Mikael reuses across other properties* (his Zinzino-Day registration site, an "omegahealth" automation) — the credentials for that pattern live in his Google account and Telegram, not in any repo.
- **Deployment**: `git push` to `main` on GitHub → GitHub Pages publishes automatically. No build/deploy pipeline to configure on a new machine.

---

## 4. Decisions Log (with reasoning)

1. **Static HTML, no framework/CMS.** No alternatives-considered discussion found in history; consistent with a single-maintainer, AI-assisted-editing personal site where framework overhead isn't justified.
2. **GitHub Pages for hosting.** Inferred from DNS + absence of any other hosting config — no explicit reasoning documented in commits. Likely chosen because it's zero-cost and lives on the same platform already used for version control.
3. **Self-hosted fonts, non-blocking Font Awesome, dropped Chinese font weights from EN pages** (commits `d3605bc`, `4c04104`, `70d018e`, `d3b23da`). Reasoning stated explicitly in commit messages: cutting mobile FCP/LCP (Core Web Vitals) — the homepage hero image is also preloaded specifically to reduce mobile LCP.
4. **Baked, indexable `/zh/` pages rather than client-side translation** (commit `dba9311`). Reasoning: a JS-only language toggle wouldn't be crawlable/indexable by search engines; SEO requires real server-rendered HTML per locale.
5. **SEO + GEO (generative-engine optimization) foundation, in two phases** (commits `1af590a`, `fdf20fd`). Reasoning: visibility in both classic search and AI-answer engines — `llms.txt` at the repo root exists specifically to support the GEO side of this.
6. **A full audit pass for brand/a11y/robustness was run and remediated** (commits `708d3cb`, `bdfbaa4` — the latter explicitly mentions "expose-private cleanup"). The commit message implies something was previously exposed that shouldn't have been and was cleaned up; no further detail is in the commit body. **Worth a fresh spot-check after migration** to confirm nothing regressed — I have not re-audited this myself in this pass (docs-only).
7. **Strategic Leader Scorecard added as a lead magnet** (commit `192149b`), deliberately reusing the existing Sheet + Apps Script + Telegram pattern rather than building new backend infrastructure. Reasoning per `scorecard-setup/SETUP.md`: fast to stand up, no server to host or maintain, consistent with automations Mikael already runs elsewhere.
8. **A Stop-hook auto-commits any dirty working tree** at the end of every Claude Code session (see `.claude/settings.local.json`, gitignored). Explains the "Auto-commit: <timestamp>" commits scattered through `git log`. Reasoning inferred: checkpoints in-progress work even if a session ends without an explicit commit.

---

## 5. Open Threads

**Waiting on Mikael:**
- Scorecard backend isn't connected yet — `scorecard.html`'s `ENDPOINT` is empty. If live lead capture is wanted, the 3-step process in `scorecard-setup/SETUP.md` (create Sheet → deploy Apps Script → paste `/exec` URL into `scorecard.html`) still needs to be done.
- `book.html` stays "Coming Soon" until the book is actually ready to sell — tied to the `BOOK_LAUNCH_PLAN.md` timeline, not a technical blocker.
- 2 commits exist locally that haven't been pushed to `origin/main` (both auto-commits, `2026-07-03` and `2026-07-07`, plus the two new handoff docs from this session). **This report did not push them** — confirm and run `git push` when ready.

**Ready to execute (no blocker, just not done):**
- Delete the `perf/async-font-loading` branch — confirmed fully merged into `main` (`git merge-base --is-ancestor` returns true), both local and remote copies are safe to delete as routine cleanup.
- Decide whether `scorecard.html` needs a `/zh/` mirror — it was added after the last visible `build_zh.py` run pattern and isn't yet confirmed to have Chinese parity.

**Blocked:**
- None visible from repo state alone. If there's something blocking on Mikael's side (editor feedback on the manuscript, endorsement replies, etc.) that isn't reflected here, it lives outside this repo — add it here once known.

---

## 6. Gotchas Learned in Sessions

- **Use Google PageSpeed Insights (PSI) for real performance numbers, not the "Ignite" widget** — Ignite has been noisy/unreliable for this site in past sessions.
- **`build_zh.py` needs `lxml`, which is only installed for system Python**, not Homebrew Python. Always run it as `/usr/bin/python3 build_zh.py`, not plain `python3 build_zh.py` (see Section 8 for exact reinstall steps on a new Mac).
- **`.claude/` is gitignored** — settings, the local dev-server launch config, and the auto-commit Stop-hook are all machine-local. They will not appear after a fresh `git clone` and must be carried over deliberately (see Migration Checklist).
- **`AI_DS_CHANNEL_FEASIBILITY.md` and the `*_PLAN.md` files are internal planning docs, not site content** — they sit at the repo root alongside the actual HTML but are never served or linked from the site. Don't confuse them with published pages when scanning the root directory.
- **Large binaries live in the working tree outside git** — the manuscript `.docx` (~5.6MB), the Gemini-generated hero image (~7.4MB), and all raw `photo_*.jpeg`/`Mikael Chew*.jpeg`/`Profile_Grayscale.jpg` originals are explicitly gitignored (`*.docx`, filename-specific rules). They exist only on disk, not in git history. **A `git clone`-only migration silently drops all of these** — this is the single biggest migration risk in this repo. See Section 7 and 8.

---

## 7. What Will NOT Survive a Simple Folder Copy or `git clone`-Only Migration

### `.env` files
**None exist in this repo.** Confirmed via `find . -iname "*.env*"` — no matches. There is nothing to carry over here by design; keep it that way (see standing rule in `CLAUDE.md`).

### Secrets and where they actually live
| Secret | Lives in | Not in this repo because |
|---|---|---|
| Telegram bot token + chat ID (Scorecard notifications) | Inside the deployed Google Apps Script (`Extensions → Apps Script` on the Google Sheet), server-side only | By design, per `scorecard-setup/SETUP.md`: "The bot token / chat ID live only inside Apps Script — never in the website." Get the token from @BotFather in Telegram if it needs to be re-created; get the chat ID via the bot's `getUpdates` endpoint. This is cloud state tied to Mikael's Google account, not a file to migrate. |
| GitHub push access | `gh` CLI, authenticated via macOS Keychain (confirmed: `gh auth status` shows `mikaelchew` account, keyring-backed, https protocol, scopes `gist read:org repo workflow`) | Keychain credentials are machine-specific and do not transfer. Must re-run `gh auth login` on the new Mac. |

### CLI logins this project relies on
- **`gh`** (GitHub CLI) — authenticated, keychain-backed, used for git push/pull over https. Re-auth required on new Mac: `gh auth login`.
- **`git`** — no separate credential store beyond what `gh` manages (`git config --local --list` shows no custom `credential.helper`; push/pull rides on `gh`'s https credentials).
- No `npm`, `vercel`, `firebase`, or other deploy CLIs are used by this project.

### Local-only assets
- **No database.** No crontab entries reference this project (`crontab -l` → none). No `launchd` agents reference it (`launchctl list` → none). The only local automation is the Claude Code Stop-hook in `.claude/settings.local.json` (gitignored — see below).
- **`.claude/` directory (gitignored, machine-local):**
  - `launch.json` — the Claude Preview dev-server launch config. **Hardcodes the full current absolute path** to `server.py`.
  - `settings.local.json` — permission allowlist plus the auto-commit Stop-hook, whose shell command also **hardcodes the current absolute project path** in a `cd` statement. The permission list additionally contains several *stale* references to an even older path (`/Users/zinzinomalaysia/Desktop/Claude_Mikael_Website`) from before this project moved to its current location — these are dead entries, harmless, but a sign this file has accumulated cruft over past migrations too.
  - Neither file is in git. Copying only via `git clone` loses both; a plain Finder/`cp -R` copy of the visible folder also loses them unless hidden files are included.
- **Installed tooling this project depends on:** `lxml` for system Python (`/usr/bin/python3`, currently 3.9.6 on this Mac), installed via `pip3 install --user lxml` into `~/Library/Python/3.9/lib/python/site-packages` — also shared by `python-pptx` and `python-docx` on this machine, so it's not exclusively this project's dependency. Homebrew's `python3` (currently 3.14 on this Mac) does **not** have `lxml` installed and will fail `build_zh.py` if used by mistake.
- **Brew packages present that relate to this project:** `gh`. (`python@3.12`, `python@3.14` are also brew-installed but are not what `build_zh.py` actually uses — see above.)

### Absolute path (`/Users/...`) references that will break on a different username/folder
Searched all tracked file types (`.html .js .css .py .md .json .gs`) — **zero absolute-path references inside anything git-tracks.** The only absolute paths in the entire project are inside the gitignored `.claude/` directory (listed above). This means: **a plain `git clone` on a new Mac needs zero path fixes** — the only path-fixing work is in `.claude/`, and only if that directory is carried over.

---

## 8. MIGRATION CHECKLIST

### On the old Mac, before migrating
1. `git push origin main` — clear the 2 outstanding local-only commits (see Section 5) so the new Mac's clone is current.
2. Decide whether to delete the merged `perf/async-font-loading` branch now or later (`git push origin --delete perf/async-font-loading && git branch -d perf/async-font-loading`) — safe either way, confirmed merged.
3. **Copy the gitignored files that only exist on disk** — a `git clone` will NOT bring these over:
   - The manuscript: `《直銷孫子兵法之不戰而勝》完整修訂版_v2.docx`
   - Raw photo originals: `Mikael Chew.jpeg`, `Mikael Chew 2.jpeg`, `Profile_Grayscale.jpg`, `Gemini_Generated_Image_*.png`, `photo_2026-04-06 *.jpeg`
   - `server.py` (trivial to recreate if lost, but faster to just copy — full contents are in this doc's Section 3 area / git history if needed)
   - The entire `.claude/` directory (settings, launch config, auto-commit hook)

   Easiest approach: copy the whole project folder as-is (Finder "duplicate," AirDrop, external drive, or `rsync -a`), rather than relying on `git clone` alone — that carries everything above in one step. If instead you `git clone` fresh on the new Mac, you must separately transfer the files listed above.

### On the new Mac
4. Install Homebrew if not already present, then:
   ```
   brew install git gh
   ```
5. Re-authenticate GitHub CLI (Keychain credentials do not transfer):
   ```
   gh auth login
   ```
   Confirm with `gh auth status` — should show the `mikaelchew` account with `repo` scope at minimum.
6. Confirm git identity is set (should already be correct if migrating the whole user account; verify if not):
   ```
   git config --global user.name
   git config --global user.email
   ```
7. Install `lxml` for system Python (needed by `build_zh.py`):
   ```
   /usr/bin/python3 -m pip install --user lxml
   ```
   If the new Mac's system Python blocks user-installs (PEP 668, common on newer macOS), add `--break-system-packages`, or install into a venv and update the `build_zh.py` invocation accordingly.
8. If `.claude/` was carried over, fix the two hardcoded absolute paths to match the new Mac's actual project path (only needed if the username or folder location differs from `/Users/zinzinomalaysia/Desktop/Work/Projects/zinzino/Mikael Chew Website`):
   - `.claude/launch.json` → `configurations[0].runtimeArgs[0]`
   - `.claude/settings.local.json` → the `cd "..."` at the start of the Stop-hook command
   - (Optional cleanup, not required for function) prune the stale `/Users/.../Claude_Mikael_Website` entries from the permissions `allow` list — they no longer match anything.
9. If the project folder was placed anywhere other than `~/Desktop/Work/Projects/zinzino/Mikael Chew Website`, update the `@AGENTS.md`-style references in the parent `Desktop/CLAUDE.md` and `Work/CLAUDE.md` (outside this repo) so the global session-start docs still resolve correctly.

### Verify it works
10. **Build/generate step:**
    ```
    /usr/bin/python3 build_zh.py
    ```
    Should complete with no errors and update timestamps under `zh/`. This is the only "build" this project has.
11. **Smoke test — local preview:**
    ```
    python3 server.py
    ```
    Open `http://localhost:8080/` — homepage should load with fonts/images intact. Then check `http://localhost:8080/zh/` — Chinese mirror should also load.
12. **Confirm git is healthy:**
    ```
    git status        # should be clean
    git remote -v      # should show https://github.com/mikaelchew/mikael-website.git
    git log --oneline -5   # should match the old Mac's history
    ```
13. Nothing further to verify for hosting/DNS — GitHub Pages and DNS are entirely server-side and unaffected by which Mac pushes to the repo.
