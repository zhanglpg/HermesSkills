"""Tests for check-market-movers module."""

import importlib

import pytest

pd = pytest.importorskip("pandas")

# The file is named with hyphens, so we must use importlib
cmm = importlib.import_module("check-market-movers")


# ---------------------------------------------------------------------------
# check_significant_events
# ---------------------------------------------------------------------------


class TestCheckSignificantEvents:
    def _make_data(self, overrides=None):
        """Build a holdings dict with all changes below threshold."""
        holdings = {}
        for ticker in cmm.PORTFOLIO:
            holdings[ticker] = {"price": 100.0, "change_pct": 0.5, "open": 99.5}
        if overrides:
            holdings.update(overrides)
        return {"holdings": holdings, "news": []}

    def test_no_events(self):
        data = self._make_data()
        should_interrupt, events = cmm.check_significant_events(data)
        assert should_interrupt is False
        assert events == []

    def test_stock_move(self):
        data = self._make_data({"NVDA": {"price": 106, "change_pct": 6.0, "open": 100}})
        should_interrupt, events = cmm.check_significant_events(data)
        assert should_interrupt is True
        stock_events = [e for e in events if e["type"] == "portfolio_move"]
        assert any(e["symbol"] == "NVDA" for e in stock_events)

    def test_etf_move(self):
        data = self._make_data({"SPY": {"price": 104, "change_pct": 4.0, "open": 100}})
        should_interrupt, events = cmm.check_significant_events(data)
        assert should_interrupt is True
        assert any(e["symbol"] == "SPY" for e in events)

    def test_china_market_move(self):
        data = self._make_data({"FXI": {"price": 95, "change_pct": -5.0, "open": 100}})
        should_interrupt, events = cmm.check_significant_events(data)
        assert should_interrupt is True
        china_events = [e for e in events if e["type"] == "china_market_move"]
        assert len(china_events) >= 1

    def test_high_severity(self):
        # threshold for stock is 5%, high is > 5% * 1.5 = 7.5%
        data = self._make_data({"GOOG": {"price": 108, "change_pct": 8.0, "open": 100}})
        _, events = cmm.check_significant_events(data)
        move = [e for e in events if e["type"] == "portfolio_move" and e["symbol"] == "GOOG"]
        assert move[0]["severity"] == "high"

    def test_none_change_skipped(self):
        data = self._make_data({"NVDA": {"price": None, "change_pct": None, "open": None}})
        should_interrupt, events = cmm.check_significant_events(data)
        nvda_events = [e for e in events if e.get("symbol") == "NVDA" and e["type"] == "portfolio_move"]
        assert len(nvda_events) == 0

    def test_news_event(self):
        data = self._make_data()
        data["news"] = [
            {
                "headline": "NVDA earnings beat",
                "source": "Reuters",
                "tickers": ["NVDA"],
                "sector": "Semiconductors",
                "significance": "high",
            }
        ]
        should_interrupt, events = cmm.check_significant_events(data)
        assert should_interrupt is True
        news = [e for e in events if e["type"] == "portfolio_news"]
        assert len(news) == 1


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_report_structure(self):
        data = {
            "holdings": {ticker: {"price": 100.0, "change_pct": 1.0, "open": 99.0} for ticker in cmm.PORTFOLIO},
            "news": [],
        }
        events = [
            {
                "type": "portfolio_move",
                "symbol": "NVDA",
                "name": "NVIDIA",
                "sector": "Semiconductors",
                "change": 6.0,
                "severity": "medium",
            }
        ]
        report = cmm.format_report(data, events)
        assert "# Portfolio Check" in report
        assert "## Summary" in report
        assert "NVDA" in report or "NVIDIA" in report
        assert "## Your Portfolio" in report
