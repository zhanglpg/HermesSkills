#!/usr/bin/env python3
"""
Hourly Portfolio Movers Check

Checks for significant events affecting YOUR portfolio holdings.
Only interrupts for portfolio-relevant events.

Usage:
    python3 scripts/check-market-movers.py [--test]

Portfolio: GOOG, NVDA, TSMC, BABA, SPY, FXI, KWEB

Data Source: Yahoo Finance (yfinance)
"""

import json
import logging
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf


def get_agent_data_dir() -> str:
    """Return the agent's data directory, defaulting to /tmp."""
    val = os.environ.get('AGENT_DATA_DIR')
    if val:
        return val
    fallback = os.path.expanduser('~/.openclaw')
    logging.warning('AGENT_DATA_DIR is not set — falling back to %s.', fallback)
    os.environ['AGENT_DATA_DIR'] = fallback
    return fallback


# ── Configuration ─────────────────────────────────────────────────────────
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_CONFIG_PATH = os.path.join(_SKILL_DIR, 'references', 'config.json')

PORTFOLIO = {
    "GOOG": {"name": "Alphabet", "sector": "Tech"},
    "NVDA": {"name": "NVIDIA", "sector": "Semiconductors"},
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Semiconductors"},
    "BABA": {"name": "Alibaba", "sector": "China Internet"},
    "SPY": {"name": "S&P 500 ETF", "sector": "US Broad Market"},
    "FXI": {"name": "China Large-Cap ETF", "sector": "China Indices"},
    "KWEB": {"name": "China Internet ETF", "sector": "China Indices"},
}

THRESHOLDS = {
    "portfolio_stock": 5.0,
    "portfolio_etf": 3.0,
    "china_exposure": 4.0,
}

OUTPUT_DIR = Path(get_agent_data_dir()) / "workspace" / "briefs" / "investment" / "hourly-checks"
STATE_FILE = Path(get_agent_data_dir()) / "workspace-finance" / "memory" / "heartbeat-state.json"
DISCORD_CHANNEL = "1478375151270887577"


def load_config(config_path=None):
    global PORTFOLIO, THRESHOLDS, OUTPUT_DIR, STATE_FILE, DISCORD_CHANNEL
    path = config_path or _DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            cfg = json.load(f)
        if 'portfolio' in cfg:
            PORTFOLIO = cfg['portfolio']
        if 'thresholds' in cfg:
            THRESHOLDS.update(cfg['thresholds'])
        if 'output_dir' in cfg:
            OUTPUT_DIR = Path(os.path.expanduser(os.path.expandvars(cfg['output_dir'])))
        if 'state_file' in cfg:
            STATE_FILE = Path(os.path.expanduser(os.path.expandvars(cfg['state_file'])))
        if 'discord_channel' in cfg:
            DISCORD_CHANNEL = cfg['discord_channel']
    except Exception as e:
        print(f"Warning: Failed to load config from {path}: {e}")


def get_market_data():
    tickers = list(PORTFOLIO.keys())
    holdings = {}
    try:
        data = yf.download(tickers, period="1d", progress=False)
        for ticker in tickers:
            try:
                close = data[('Close', ticker)].iloc[-1] if len(data) > 0 else None
                open_price = data[('Open', ticker)].iloc[-1] if len(data) > 0 else None
                if close is not None and open_price is not None and open_price > 0:
                    change_pct = ((close - open_price) / open_price) * 100
                else:
                    change_pct = None
                holdings[ticker] = {
                    "price": float(close) if close is not None else None,
                    "change_pct": float(change_pct) if change_pct is not None else None,
                    "open": float(open_price) if open_price is not None else None,
                }
            except Exception as e:
                holdings[ticker] = {"price": None, "change_pct": None, "open": None, "error": str(e)}
    except Exception as e:
        print(f"Warning: Failed to fetch market data: {e}")
        holdings = {ticker: {"price": None, "change_pct": None, "open": None} for ticker in tickers}

    return {
        "holdings": holdings,
        "news": [],
        "fetched_at": datetime.now().isoformat(),
    }


def check_significant_events(data):
    events = []
    should_interrupt = False

    for ticker, holding in data.get("holdings", {}).items():
        if ticker not in PORTFOLIO:
            continue
        change = holding.get("change_pct")
        info = PORTFOLIO[ticker]
        if change is None:
            continue
        is_etf = ticker in ["SPY", "FXI", "KWEB"]
        threshold = THRESHOLDS["portfolio_etf"] if is_etf else THRESHOLDS["portfolio_stock"]
        if abs(change) >= threshold:
            severity = "high" if abs(change) > threshold * 1.5 else "medium"
            events.append({
                "type": "portfolio_move",
                "symbol": ticker,
                "name": info["name"],
                "sector": info["sector"],
                "change": change,
                "severity": severity,
            })
            should_interrupt = True

    your_sectors = set(info["sector"] for info in PORTFOLIO.values())
    for news in data.get("news", []):
        news_sector = news.get("sector")
        news_tickers = news.get("tickers", [])
        affects_portfolio = (
            news_sector in your_sectors or
            any(t in PORTFOLIO for t in news_tickers)
        )
        if affects_portfolio and news.get("significance") in ["high", "medium"]:
            related = [t for t in news_tickers if t in PORTFOLIO]
            events.append({
                "type": "portfolio_news",
                "headline": news.get("headline"),
                "source": news.get("source"),
                "related_tickers": related,
                "sector": news_sector,
                "severity": news.get("significance", "medium"),
            })
            if news.get("significance") == "high":
                should_interrupt = True

    for china_etf in ["FXI", "KWEB"]:
        etf_data = data.get("holdings", {}).get(china_etf, {})
        etf_change = etf_data.get("change_pct")
        if etf_change is not None and abs(etf_change) >= THRESHOLDS["china_exposure"]:
            events.append({
                "type": "china_market_move",
                "symbol": china_etf,
                "change": etf_change,
                "severity": "high" if abs(etf_change) > 6 else "medium",
                "note": "Affects China portfolio (BABA, FXI, KWEB)",
            })
            should_interrupt = True

    return should_interrupt, events


def format_report(data, events):
    now = datetime.now()
    report = []
    report.append(f"# Portfolio Check - {now.strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## Summary")
    report.append(f"- Check Time: {now.isoformat()}")
    report.append(f"- Events Found: {len(events)}")
    report.append(f"- Interrupt Required: **{'Yes' if events else 'No'}**")
    report.append("")

    if events:
        report.append("## 🚨 Portfolio Events")
        report.append("")
        for event in events:
            if event["type"] == "portfolio_move":
                report.append(f"- **{event['symbol']}** ({event['name']}): {event['change']:+.2f}%")
                report.append(f"  - Sector: {event['sector']} | Severity: {event['severity']}")
            elif event["type"] == "portfolio_news":
                tickers = ", ".join(event.get("related_tickers", []))
                report.append(f"- **News**: {event['headline']}")
                report.append(f"  - Related: {tickers} | Sector: {event.get('sector', 'N/A')}")
            elif event["type"] == "china_market_move":
                report.append(f"- **{event['symbol']}**: {event['change']:+.2f}% ({event['note']})")
        report.append("")

    report.append("## Your Portfolio")
    report.append("")
    report.append("| Ticker | Name | Sector | Price | Change |")
    report.append("|--------|------|--------|-------|--------|")
    for ticker, info in PORTFOLIO.items():
        holding = data.get("holdings", {}).get(ticker, {})
        price = holding.get("price")
        change = holding.get("change_pct")
        display_ticker = "TSMC" if ticker == "TSM" else ticker
        price_str = f"${price:.2f}" if price is not None else "N/A"
        if change is not None:
            change_str = f"{change:+.2f}%"
            if change > 0:
                change_str = f"🟢 {change_str}"
            elif change < 0:
                change_str = f"🔴 {change_str}"
            else:
                change_str = f"⚪ {change_str}"
        else:
            change_str = "N/A (Market Closed?)"
        report.append(f"| {display_ticker} | {info['name']} | {info['sector']} | {price_str} | {change_str} |")

    return "\n".join(report)


def save_report(report, timestamp):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = timestamp.strftime("%Y-%m-%d-%H-check.md")
    filepath = OUTPUT_DIR / filename
    filepath.write_text(report)
    return filepath


def update_state(events):
    display_holdings = []
    for ticker in PORTFOLIO.keys():
        display_ticker = "TSMC" if ticker == "TSM" else ticker
        display_holdings.append(display_ticker)

    state = {
        "marketMoversCheck": {
            "lastCheck": datetime.now().isoformat(),
            "lastSignificantEvent": events[0] if events else None,
            "checkCount": 1,
        },
        "portfolio": {
            "holdings": display_holdings,
            "interruptThresholds": THRESHOLDS,
        },
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    load_config()
    print(f"[{datetime.now().isoformat()}] Starting portfolio check...")
    data = get_market_data()
    should_interrupt, events = check_significant_events(data)
    update_state(events)

    if events:
        now = datetime.now()
        report = format_report(data, events)
        filepath = save_report(report, now)
        print(f"Report saved to: {filepath}")
        print(f"\n⚠️ PORTFOLIO EVENTS DETECTED ({len(events)}):")
        for event in events:
            if event["type"] == "portfolio_move":
                print(f"  - {event['symbol']}: {event['change']:+.2f}%")
            elif event["type"] == "portfolio_news":
                print(f"  - News: {event['headline']}")
            else:
                print(f"  - {event}")
        return 1
    else:
        print(f"\n✓ No portfolio events (checked {len(PORTFOLIO)} holdings) - no report saved")
        return 0


if __name__ == "__main__":
    sys.exit(main())
