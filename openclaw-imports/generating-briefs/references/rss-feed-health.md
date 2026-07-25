# RSS Feed Health — AI Tech Brief (updated July 2026)

Status of each configured RSS feed as of 2026-07-13 session.

## Healthy (returning fresh content)

| Feed | Status | Items | Notes |
|------|--------|-------|-------|
| **Simon Willison's Weblog** | ok | 5 items (Jul 11–12) | Consistently the most reliable RSS source. Rich summaries, daily updates. |

## Empty / Zero Items

| Feed | Status | Items | Notes |
|------|--------|-------|-------|
| Import AI | ok | 0 items | Feed returns 200 but no recent items — Jack Clark may have paused newsletter. |
| Latent Space | ok | 0 items | Feed returns 200 but no items. May require a different URL. |
| Anthropic | ok | 0 items | Feed returns 200 but no items. Direct browser visit to anthropic.com/news may be more reliable. |
| Hugging Face | ok | 0 items | Feed returns 200 but no items. Navigate to huggingface.co/blog directly for post dates. |

## Broken

| Feed | Status | Error | Notes |
|------|--------|-------|-------|
| TLDR AI | error | 404 Not Found | URL `tldr.tech/feed/ai` broken again after previous fix (was `tldr.tech/rss` → 308 → `tldr.tech/feed/ai`). May have changed URL again. |
| OpenAI | error | 403 Forbidden | OpenAI RSS is now access-controlled. Skip entirely — rely on TechCrunch/Ars/HN for OpenAI news. |
| The Neuron | error | XML parse error | `theneuron.beehiiv.com/rss` returns malformed XML. Low priority — The Neuron content is often days old. |

## Strategy

Only Simon Willison is reliable for fresh content via RSS. All other feeds are either stale, broken, or blocked. For AI lab news (Anthropic, OpenAI, Hugging Face), direct browser navigation produces better results than RSS. For newsletter content (TLDR, The Neuron, Import AI), the existing pitfall "Most newsletter RSS feeds will fail" remains accurate — don't spend time debugging individual feed failures.
