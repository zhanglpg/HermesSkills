---
name: options-strategy-builder
description: Price options strategies (collars, covered calls, spreads).
---

# Options Strategy Builder

Construct and price options strategies against a share position using live (delayed) market data. Validated data pipeline and collar methodology below.

## Data pipeline (in order)

1. **Spot price + 52w range**: Yahoo chart API, no auth:
   `curl -s -H 'User-Agent: Mozilla/5.0' 'https://query1.finance.yahoo.com/v8/finance/chart/TICKER?interval=1d&range=5d'`
   → `chart.result[0].meta` has `regularMarketPrice`, `fiftyTwoWeekLow/High`, `regularMarketTime`.
2. **Full option chain (bid/ask/IV/OI/greeks)**: CBOE delayed quotes, no auth:
   `curl -s -H 'User-Agent: Mozilla/5.0' -H 'Accept: application/json' 'https://cdn.cboe.com/api/global/delayed_quotes/options/TICKER.json'`
   → `data.current_price` (spot), `data.options[]` where each row's `option` symbol is `TICKER+YYMMDD+C/P+strike*1000` (8-digit zero-padded). Fields: `bid`, `ask`, `last_trade_price`, `iv`, `open_interest`, `volume`, `delta`, `gamma`, `theta`, `vega`, `theo`. Works after hours — returns last quoted bid/ask, unlike yfinance.
3. **Expiration list + historical vol**: `yfinance` (`Ticker.options`, `Ticker.history`). yfinance `option_chain()` bid/ask come back as 0.00 outside market hours — never trust yfinance for option quotes; use it only for expirations and price history.

Pitfalls:
- CBOE cdn intermittently answers with a 307 redirect HTML page — always fetch with `curl -sL` (follow redirects); a JSONDecodeError starting with `<html>` means you parsed the redirect body.
- Parse the option symbol by stripping the LEADING ALPHA PREFIX generically, not a fixed offset: tickers vary in length (GOOG=4, GOOGL=5) and a fixed `sym[4:]` silently produces garbage keys on the 5-char class. Same company's share classes price ~1% apart (voting premium) — always value a position against its OWN chain.
- Yahoo `v7/finance/options/*` returns `{"error":{"code":"Unauthorized","description":"Invalid Crumb"}}` — it requires a cookie/crumb dance. Use CBOE instead; do not fight the crumb.
- yfinance IV field degenerates to near-zero values after hours — garbage, not real IV. Cross-check against CBOE `iv`.
- Check `date -u` before quoting prices: CBOE/Yahoo delayed data is last-trade-based after hours; label quotes with their timestamp in the output.
- Risk-neutral expiry probabilities: P(S_T < K) = N(−d2) and P(S_T > K) = N(+d2), d2 = (ln(S/K) + (r − σ²/2)·T)/(σ·√T). The sign flips silently — sanity-check that below-floor / between-strikes / above-cap probabilities sum to 100% with a positive middle; a negative middle or a >50% tail on an OTM strike means the sign is wrong.
- Quote tail risk as 5% CVaR (mean of the worst 5% of lognormal samples), unhedged vs hedged, integrated over ONE shared distribution — the collar's value proposition is tail reduction and a single VaR number understates it. Report the EV difference the same way so the user sees the insurance premium explicitly.

## Timing assessment (compute before recommending a build window)

1. **HV level + percentile**: 21-day annualized vol of daily log returns, and its percentile within the trailing 252 HV21 readings. Low percentile (<30%) = protection cheap, good window to buy puts; high (>70%) = options rich, favor the selling side.
2. **IV term structure**: ATM IV per expiration from the CBOE chain; flag the step between pre-event and post-event expirations (earnings). Selling the call on the high-IV side of the step subsidizes the put — that gap is the zero-cost-collar window.
3. **Skew**: put IV minus call IV in points at the candidate strikes. Mild (<3pts) = downside protection not bid up; steep = widen the floor or use a put spread instead of a bare put.
Report all three plus whether a known event (earnings date — confirm via web search, label unconfirmed) falls inside the window, as the timing verdict.

## Collar construction method

1. Contracts = shares / 100 (confirm round lot; if not, state the unhedged remainder).
2. Pick 2-3 expirations ~60-130 DTE. Screen put strikes at ~-8% to -15% from spot, call strikes at ~+10% to +20%. Prefer strikes with OI in the thousands (liquid exits, tight spreads) and round numbers.
3. Price each candidate **mid-to-mid** for net credit/debit, and also compute the **worst-case fill** (buy at ask, sell at bid) — report both.
4. Build 3-4 named structures (recommended zero/near-zero-cost, tighter protection, wider upside, longer-dated) with floor/cap/max-loss/max-gain for each. Lead with one recommendation and say why.
5. Produce an expiry P&L table for the recommended structure across ~15 spot scenarios (deep below floor → far above cap), comparing to unhedged.
6. Sanity checks to mention: earnings dates inside the window (IV premium + gap risk), covered-call status (no naked risk), dividends vs early assignment, and roll-up/out option if the short call is threatened.
7. Report format: plain-text sections — market data snapshot, recommended structure (legs with strikes/mids/OI), net credit both fills, floor/cap/max P&L, scenario table, alternatives priced the same way, caveats. Keep it numeric and dense; no filler. When the user asks for a report/文档 deliverable rather than a chat answer, publish it as a single-file React dashboard on zhanglpg.github.io via the `single-file-react-gh-pages` skill: sections 时机 / 构建(推荐结构) / 备选对比 / 损益情景 / 维持规则 / 残余风险, generated `data.js` from the priced candidates, SVG charts for price+HV, IV term structure, and expiry payoff vs unhedged. This user expects EVERY SVG chart in the dashboard to support mouse-hover tooltips (crosshair + floating data card: x value, each series' y, day-over-day delta; flip the card left past ~62% width; reuse the handler for touch; test hiding by dispatching `mouseout` not `mouseleave` — React synthesizes leave from mouseout).
8. Maintenance: every collar deliverable includes the post-build playbook (calendar rolling, trigger rules, annual re-evaluation) from `references/collar-maintenance.md`, condensed into the report and summarized in chat.

Strike selection heuristic: floor ≈ 1.3 standard deviations below spot over the window at current IV (spot × exp(-1.3 × IV × √(DTE/365))) is a reasonable anchor; cap just below a technical level (e.g., 52-week high) so only a new-high melt-up is sacrificed.

## Daily-refresh collar report pattern (GOOG implementation)

For a recurring report, split numbers from narrative:
- `refresh.py` (in the Pages repo, versioned with the report) does ALL data work: fetch Yahoo+CBOE, recompute candidates/probs/scenarios/triggers, emit KEY=VALUE stdout lines, and regenerate `data.js` including auto-narrative strings (why-strikes, bull/bear signals, timeline, summary). Deterministic script = no LLM hallucination in the numbers.
- Hysteresis on strike selection: keep current structure unless a leg drifts >2.5% from target moneyness or DTE <45 (then roll to ~120 DTE and re-anchor), so daily refreshes don't flip-flop strikes. Persist in `state.json`.
- Preserve curated fields (timing.conclusion, disclaimer, earnings date) by reading previous data.js and carrying them forward; the cron agent rewrites them only when FLAGS show WARN_ROLL/REANCHORED/CREDIT_NEG.
- Emit a TRIGGERS hit= line (spot vs cap-3%/floor+3%) so the cron agent can flag actionable days without reasoning over raw numbers.
- Idempotency: if CBOE/Yahoo quote date == state.lastQuoteDate, print NO_CHANGE and exit 0 — weekends/holidays send a one-liner instead of a full report.
- Hermes cron: `script` param must be a filename under ~/.hermes/scripts/ (absolute paths rejected); use a thin wrapper there that subprocess-runs the repo script. Schedule `25 8 * * *` = daily 8:25 Beijing (US close ~6:25-7:25 CST, so data is settled).
- Yahoo meta.previousClose is unreliable on some responses (returned 160 for a 343 stock = 2y-ago chartPreviousClose); derive prev close from the closes series — but check whether the series' LAST bar is the quote date first (compare its timestamp in ET): if yes, prev close = pairs[-2]; if no (the settled series lags pre-market/overnight runs), prev close = pairs[-1]. Blindly taking pairs[-2] double-counts a day when the series hasn't caught up, inflating the reported daily change.
- Intraday vs settled: Yahoo regularMarketPrice during ET market hours is a LIVE price and the chart's last bar is today's partial bar. Detect (ET weekday 09:30-16:00), label output as intraday, and do NOT record lastQuoteDate for intraday runs — otherwise the evening settled-close refresh gets suppressed by the idempotency check and stale numbers persist until next morning.

## Switching to maintenance mode (user filled a real collar)

When the user reports an actual fill (often at DIFFERENT strikes than recommended — record what they hold, not what you suggested):
- Add `mode: "maintenance"` + a `live` block to state.json: expiry, put, call, contracts, entryDate, entrySpot, entry_credit. The refresh script must FREEZE these strikes — no re-anchoring, no roll logic against live legs; only monitoring. Screening-mode reanchoring would silently fight the real position.
- Ask the user for entry fill (net credit/debit per share + entry spot) — without it, option-leg mark-to-market P&L is uncomputable; emit `mtmPnl: null` / "待补录" rather than assuming 0, and guard every format string against None (f-string `:+.2f` on None crashes the whole refresh).
- Cross-check the user's reported entry against option economics before recording it: an OTM collar whose put strike is CLOSER to spot than the call strike cannot open at a net credit (you pay more for the nearer put than you collect for the farther call). If the reported sign contradicts the day's mids, record the market-consistent value, flag it in the page narrative as 待核对, and ask the user to check the broker confirmation — do not silently trust the verbal fill.
- MTM sign convention: P&L = cash at open + cash to close, both signed (entry_credit >0 = received credit; open_cost = put_mid − call_mid = proceeds if you sold the put and bought back the call now). Sanity check: opening and closing at identical prices must give P&L = 0 — an E−C formula double-counts and fails this test.
- Multiple positions (e.g. both share classes of the same company): store `livePositions` as an array in state.json (id/ticker/shares/expiry/put/call/entryDate/entry_credit each), fetch and cache one chain per ticker, render one card per position plus an aggregate card (total stock value, summed net-delta stock-equivalent, summed option-leg MTM), and emit per-position LIVE[TICKER] lines plus a LIVE_TOTAL line in the cron stdout. The cron prompt must enumerate every position so the daily brief covers them all; a roll/close edits only that array entry.
- Compute and emit live tracking per run: both legs' mid/delta/IV, net delta (1 + putΔ − callΔ, × shares = stock-equivalent exposure), cost-to-close both legs, MTM vs entry credit, trigger lines from LIVE strikes (cap−3% / floor+3%) with % distance, roll-window date (expiry−30d), and a status class: HOLD / NEAR_CAP / CALL_ITM / NEAR_FLOOR / PUT_ITM. Status ≠ HOLD → WARN_LIVE_* flag so the cron agent escalates.
- Make the recommended-structure candidate (A) track the live strikes so scenario tables, probabilities, payoff chart and CVaR all describe the REAL position — and price those artifacts against the ACTUAL entry cash flow, not the current mid: carry a `cash` field (= entry_credit in maintenance mode) through data.js and consume it in the scenario/EV/CVaR lambdas and in the chart JS (guard `A.cash` undefined → fall back to net_mid). The mid-based net drifts daily and misstates realized position economics.
- Once maintenance mode is live, PRUNE the dashboard to the maintenance view — this user explicitly asked to drop the build-strategy content after filling: remove the timing-signals / recommended-build + execution-details / alternative-structures sections (and their nav entries), renumber the remaining chapters, and keep market context (IV term structure = roll-pricing input), expiry P&L + probabilities, maintenance rules, and residual risk. Do NOT just append a live panel to the build report; build content is dead weight once a position exists.
- After the user confirms a disputed entry cash-flow sign, remove the 待核对 caveat from the narrative fields and rewrite the state.json entryNote — don't leave stale uncertainty markers on a public report.
- Rewrite the cron prompt for the new job identity: daily report becomes a maintenance brief (status pill, leg mids, net delta, trigger distances, ⚠️ action lines from the playbook), not a build recommendation. Suppress screening-only flags (e.g. WARN_CREDIT_NEG) in maintenance mode.
- GitHub Pages CDN serves stale data.js for minutes after push (max-age=600, x-cache HIT) even when raw.githubusercontent.com already shows the new content — verify via raw URL + cache-busting query param and last-modified header; do NOT re-push assuming the deploy failed.
