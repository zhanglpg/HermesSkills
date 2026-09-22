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
7. Report format: plain-text sections — market data snapshot, recommended structure (legs with strikes/mids/OI), net credit both fills, floor/cap/max P&L, scenario table, alternatives priced the same way, caveats. Keep it numeric and dense; no filler. When the user asks for a report/文档 deliverable rather than a chat answer, publish it as a single-file React dashboard on zhanglpg.github.io via the `single-file-react-gh-pages` skill: sections 时机 / 构建(推荐结构) / 备选对比 / 损益情景 / 维持规则 / 残余风险, generated `data.js` from the priced candidates, SVG charts for price+HV, IV term structure, and expiry payoff vs unhedged.
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
- Yahoo meta.previousClose is unreliable on some responses (returned 160 for a 343 stock = 2y-ago chartPreviousClose); derive prev close from the closes series instead: pairs[-1] is today's bar (live intraday if market open), pairs[-2] is the prior settled close.
- Intraday vs settled: Yahoo regularMarketPrice during ET market hours is a LIVE price and the chart's last bar is today's partial bar. Detect (ET weekday 09:30-16:00), label output as intraday, and do NOT record lastQuoteDate for intraday runs — otherwise the evening settled-close refresh gets suppressed by the idempotency check and stale numbers persist until next morning.
