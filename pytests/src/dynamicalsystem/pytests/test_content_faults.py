"""content.GitHub taxonomy, offline: requests.get and settings are mocked, so
these run with no network and pin the exact classification that stopped today's
silent outage -- a chart that returns 200 but will not parse is CORRUPT, not
'not written yet'.
"""
from json import JSONDecodeError
from types import SimpleNamespace
from pytest import raises

import dynamicalsystem.gazette.content as content_mod
from dynamicalsystem.gazette.content import (
    GitHub,
    ChartCorrupt,
    ChartUnavailable,
    ReviewNotReady,
)


def _response(ok=True, status=200, json_exc=None, data=None, url="http://t/c.json"):
    def _json():
        if json_exc is not None:
            raise json_exc
        return data

    return SimpleNamespace(ok=ok, status_code=status, text="", url=url, json=_json)


def _patch(monkeypatch, response):
    monkeypatch.setattr(content_mod, "get", lambda *a, **k: response)
    monkeypatch.setattr(
        content_mod,
        "settings",
        lambda: SimpleNamespace(github_url="http://t/", github_token=""),
    )


def test_unparseable_chart_is_chartcorrupt(monkeypatch):
    # HTTP 200 but the body is not valid JSON -- today's dropped-comma incident
    _patch(monkeypatch, _response(json_exc=JSONDecodeError("Expecting ','", "", 0)))
    with raises(ChartCorrupt):
        GitHub("tQ26.H", 98)


def test_non_list_chart_is_chartcorrupt(monkeypatch):
    _patch(monkeypatch, _response(data={"not": "a list"}))
    with raises(ChartCorrupt):
        GitHub("tQ26.H", 1)


def test_http_error_is_chartunavailable(monkeypatch):
    # 404 (missing file) or 401 (expired PAT) -- a fault, no longer a silent None
    _patch(monkeypatch, _response(ok=False, status=404))
    with raises(ChartUnavailable):
        GitHub("tQ26.H", 1)


def test_placing_past_end_is_reviewnotready(monkeypatch):
    _patch(monkeypatch, _response(data=[{"artist": "A"}]))  # one item, ask for 5
    with raises(ReviewNotReady):
        GitHub("tQ26.H", 5)


def test_good_item_is_returned_and_graded(monkeypatch):
    item = {"artist": "A", "work": "W", "review": "r", "verdict": "Buy."}
    _patch(monkeypatch, _response(data=[item]))
    gh = GitHub("tQ26.H", 1)
    assert gh.item == item
    assert gh.classify() == "ok"
    assert gh.validate_content() is True
