from pathlib import Path
from types import SimpleNamespace

import pytest

from infocars.assistant import ask, run_tool
from infocars.db import build_database, market_price, price_position

DATA = Path(__file__).resolve().parent.parent / "data" / "sample_listings.csv"


@pytest.fixture(scope="module")
def db():
    return build_database(DATA)


def test_quality_report_adds_up(db):
    _, report = db
    assert report["raw"] == report["matched"] + report["bad_price"] + report["incomplete"] + report["outliers"]
    assert report["outliers"] > 0  # the sample includes prices typed without their last digit
    assert report["matched"] / report["raw"] > 0.9
    assert report["raw_model_spellings"] > report["canonical_models"] == 7


def test_market_price(db):
    conn, _ = db
    result = market_price(conn, "onix", "ltz", 2023)
    assert result["comparables"] > 0
    assert result["p25_price_brl"] <= result["median_price_brl"] <= result["p75_price_brl"]


def test_price_position(db):
    conn, _ = db
    market = market_price(conn, "onix", "ltz", 2023)
    high = price_position(conn, "onix", "ltz", 2023, market["p75_price_brl"] * 1.2)
    assert high["position"] == "above market"
    assert high["gap_to_median_brl"] > 0


def test_unknown_car_returns_no_comparables(db):
    conn, _ = db
    assert market_price(conn, "ka", "se", 2019) == {"comparables": 0}


def test_run_sql_refuses_raw_table(db):
    conn, _ = db
    assert "refused" in run_tool(conn, "run_sql", {"sql": "SELECT * FROM raw_listings"})["error"]


class FakeClient:
    """Plays back two turns: the model asks for a tool, then answers with text."""

    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(type="tool_use", id="t1", name="market_price",
                                        input={"model": "onix", "version": "ltz", "year": 2023})
            return SimpleNamespace(stop_reason="tool_use", content=[tool_call])
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="About R$ 85k.")])


def test_ask_runs_the_tool_and_caches_the_prompt(db):
    conn, _ = db
    client = FakeClient()
    assert ask("How much is a 2023 Onix LTZ?", conn, client=client) == "About R$ 85k."

    tool_result = client.calls[1]["messages"][-1]["content"][0]
    assert tool_result["type"] == "tool_result" and '"comparables"' in tool_result["content"]
    assert client.calls[0]["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert client.calls[0]["tools"][-1]["cache_control"] == {"type": "ephemeral"}
