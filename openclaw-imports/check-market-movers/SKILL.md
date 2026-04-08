---
name: check-market-movers
description: "Monitors portfolio holdings (GOOG, NVDA, TSMC, BABA, SPY, FXI, KWEB) hourly for significant price moves using Yahoo Finance data. Only interrupts for portfolio-relevant events exceeding configurable thresholds. Use when setting up automated portfolio alerts, hourly market checks, or significant move notifications."
---

# Check Market Movers Skill

Hourly portfolio monitoring that checks for significant price moves in tracked holdings. Only interrupts when events exceed configured thresholds.

## Quick Start

```bash
# Run manually
python3 ~/.hermes/skills/openclaw-imports/check-market-movers/scripts/check-market-movers.py

# The script reads config.json from its parent directory automatically
```

## Portfolio Tracked

| Ticker | Name | Sector | Interrupt Threshold |
|--------|------|--------|---------------------|
| GOOG | Alphabet | Tech | >5% |
| NVDA | NVIDIA | Semiconductors | >5% |
| TSM | Taiwan Semiconductor | Semiconductors | >5% |
| BABA | Alibaba | China Internet | >5% |
| SPY | S&P 500 ETF | US Broad Market | >3% |
| FXI | China Large-Cap ETF | China Indices | >4% |
| KWEB | China Internet ETF | China Indices | >4% |

## How It Works

1. **Fetch Data** — Calls Yahoo Finance API (yfinance) for real-time prices
2. **Calculate Changes** — Computes intraday % change from open/close
3. **Check Thresholds** — Compares moves against portfolio-specific thresholds
4. **Report Events** — Only saves report and sends message if significant events detected

**Design principle:** Silent by default. No spam on normal days.

## Dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| Python 3 | Script runtime | Built-in |
| yfinance | Yahoo Finance API | `pip install yfinance` |
| pandas | Data handling | Installed with yfinance |

## Configuration

Edit `references/config.json` to customize portfolio, thresholds, and output paths.

## Scheduling

**Target schedule:** `0 22-23 * * 1-5` and `0 0-7 * * 1-6` (Asia/Shanghai)
- Shanghai Time: 10:00 PM - 7:00 AM (Mon-Sat)
- US Eastern Time: 9:30 AM - 4:00 PM (Mon-Fri)

## Output

Silent when no events. When events detected, saves a markdown report and prints a summary.
