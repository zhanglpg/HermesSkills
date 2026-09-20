# Collar maintenance playbook (post-build)

A collar is not set-and-forget. Three loops: calendar rolling, event triggers, annual re-evaluation.

## Loop 1 — calendar rolling (the main cycle)

- **Roll at 21–30 DTE remaining.** Theta decay is steepest in the last 30 days; closing the old legs and selling the next cycle then captures the most time value and avoids expiry-week gamma and assignment uncertainty.
- **Close-and-reopen, never single-leg rolls.** The new cycle's strikes must be re-anchored to the current spot, so a combined close order + fresh combo order is cleaner and slippage on liquid large-cap chains is negligible.
- **Re-anchor strikes to the new spot, not the old cost basis**: put back at −10% to −13%, call at the nearest technical resistance/round number above. Protection follows market value, not entry price.
- **Default cycle 90–130 DTE** (monthly/quarterly expirations), ~3–4 rolls per year. Shorten to ~60 DTE only when the term structure shows far months >5pts richer (contango); lengthen when far months are cheap.
- Each roll must cover any known event (earnings) inside the new window — never roll into a window that expires just before an event and leaves the position naked through it.

## Loop 2 — event triggers

| Trigger | Action | Why |
|---|---|---|
| Spot ≥ call strike −3%, >30 DTE left | Evaluate roll up: buy back the short call, sell a higher strike, move the put up in the same combo, keep net credit ≥ 0 | Preserve upside; floor rises with the position |
| <21 DTE and spot > call strike | Either roll up-and-out, or accept assignment at the cap (it is a pre-planned take-profit) and re-establish position + new collar with proceeds | Avoids unplanned ex-dividend assignment; the cap sale was the plan |
| Spot ≤ put strike +3% | Do NOT panic-close — protection is working. If the drop is idiosyncratic (not market-wide), roll down: sell the deep-ITM put (delta ≈ −0.8, rich), buy a lower-strike put, move the call down | Monetizes used-up insurance into a cheaper lower floor |
| ATM IV spikes >40% into an event, not yet positioned | Wait for post-event IV crush to build; if already collared, optionally sell a small extra near-dated OTM call (≤⅓ size) into the spike | Sellers have positive expectancy at event IV peaks; keep the main structure intact |
| Company-level shock (M&A, split, ruling, CEO change) | Same-day re-evaluation: if the long-term thesis changed, reduce SHARES, not options; if only volatility changed, confirm the collar still spans the new range | Options hedge price risk, not thesis risk |
| HV21 < 15% (deep calm) | Next roll: buy closer puts (−8% to −10%) | Protection is cheap in low-vol regimes; tighten the floor for free |

## Loop 3 — annual re-evaluation

- **Concentration first**: if the position grew past the portfolio's comfort share, the fix is selling shares, not adding options — let the short call get assigned as pre-planned trimming, or cut shares and resize the collar proportionally (contracts = new shares / 100). A collar manages volatility, not concentration.
- **Hedge ratio is an annual decision**: collaring half the position (e.g. 29 of 58 contracts) halves cost and keeps upside participation; set it from drawdown tolerance, not from a price view.
- **Each January compare alternatives**: renew collar vs long-dated LEAPS put (no cap, multi-year lock) vs put-spread collar (sell a further-OTM put under the long put: ~40% cheaper, gives up protection below the second strike). The year's HV/IV regime decides.
- **Log actual fills vs mid every roll**; if slippage exceeds ~$0.50/share/round, tighten limits and split orders further.
