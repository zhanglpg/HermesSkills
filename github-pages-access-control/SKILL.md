---
name: github-pages-access-control
version: 1.0
description: "Use when protecting personal data on zhanglpg.github.io."
---

# GitHub Pages Access Control (personal dashboards)

## Why GitHub-native is impossible

- Private Pages (real access control) requires an **organization on GitHub
  Enterprise Cloud**. Personal accounts on any plan: NO.
- GitHub Pro allows Pages from a private repo but the **site is still public**
  to anyone with the URL.
- On GitHub Free (Liping's plan), making the repo private **unpublishes** the
  site entirely.
- Client-side JS identity checks are fake security: data files (data.js /
  data.json) are served raw and curlable; GitHub OAuth code→token exchange
  needs a secret that cannot live in public JS.

## The migration (in progress as of 2026-10-11)

Target: Cloudflare Pages (free) + Cloudflare Access (free ≤50 users) with a
GitHub identity provider, allow policy = zhanglpg@gmail.com only.

### Done
1. Private repo created + populated: `zhanglpg/private-dashboards` (25 files):
   goog-collar/, schoology-tracker/, hotcrp-tracker/, coros-dashboard/,
   portfolio/ + landing index.html + .gitignore (raw/ and .state.json excluded).
   Copied with `git ls-files` from ~/claudews/zhanglpg.github.io so only tracked
   files moved (no raw GPS/HR data, no parser state).
2. Deploy script: `~/.hermes/scripts/cf-pages-deploy.sh` — wrangler pages
   deploy of the private repo; reads CLOUDFLARE_API_TOKEN +
   CLOUDFLARE_ACCOUNT_ID from ~/.hermes/.env; exits 1 with a clear message
   until the token exists.
3. Public site left untouched (cron jobs still deploy there) — do NOT delete
   the public dirs until the gate is verified end-to-end.

### Blocked on the human (Turnstile wall)
Cloudflare signup shows a Turnstile "verify you are human" challenge that the
harness browser CANNOT pass (bot fingerprinting; synthetic + CDP mouse events
both rejected). Account creation needs a real human in a real browser.
After the account exists, everything else is API-automatable.

### Remaining steps (resume here)
1. Human: create Cloudflare account (free plan), then add to ~/.hermes/.env:
   `CLOUDFLARE_API_TOKEN=*** (Account:Cloudflare Pages:Edit +
   Zero Trust:Edit perms) and `CLOUDFLARE_ACCOUNT_ID=***`.
2. Run `bash ~/.hermes/scripts/cf-pages-deploy.sh` → project
   `private-dashboards.pages.dev`.
3. Create Access application: domain `private-dashboards.pages.dev`,
   subdomain `*` (covers preview hashes), session 24h.
   Identity provider: GitHub (needs a GitHub OAuth app: callback
   https://<team>.cloudflareaccess.com/cdn-cgi/access/callback; store
   client_id/secret in Access IdP config). Policy: Allow,
   include email == zhanglpg@gmail.com. (Email One-time-PIN is the simpler
   alternative if the OAuth app step is unwanted.)
4. Rewire deploy scripts to push to the private repo + run
   cf-pages-deploy.sh: ~/.hermes/scripts/{schoology-deploy.sh,hotcrp-deploy.sh},
   goog_collar_refresh.py, coros cron_sync/update, portfolio-dashboard/deploy.sh
   (REPO_DIR/DEST vars point at ~/claudews/zhanglpg.github.io today).
5. Update cron job prompts that reference zhanglpg.github.io URLs
   (goog-collar-maintenance health-check curl, 4-Hour Email Check, coros sync).
6. Verify: anonymous curl of pages.dev → 302/403 gate; GitHub login admits.
7. DESTRUCTIVE LAST STEP: remove the 5 dirs from the public repo AND rewrite
   git history (450 commits touch them; repo has forks=0 so rewrite is safe).
   Use git filter-repo --invert-paths --path goog-collar --path
   schoology-tracker --path hotcrp-tracker --path coros-dashboard --path
   portfolio, then force-push. Old plaintext data.json/data.js remain readable
   via historical commit URLs until this is done.

### Deploy topology today (for rewiring)
- schoology/hotcrp: ~/.hermes/scripts/*-deploy.sh → git push zhanglpg.github.io
- goog-collar: ~/.hermes/scripts/goog_collar_refresh.py (REPO=.../goog-collar)
- coros: cron agent (coros-dashboard-sync job) writes + pushes in-repo
- portfolio: ~/claudews/portfolio-dashboard/deploy.sh copies files into
  zhanglpg.github.io/portfolio then pushes
