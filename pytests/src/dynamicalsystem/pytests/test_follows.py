"""The leader/follower rule (pure unit tests -- publishers and the watermark
file are faked, nothing touches GitHub, Signal or Bluesky).

A route may declare `follows: <leader>`. The contract:
  - a follower publishes placing P only if its leader's placing, as of the
    START of the sweep, is strictly less than P (the leader posted P earlier);
  - a follower that has drawn level holds for one sweep while the leader goes
    ahead, then publishes the next sweep;
  - a leader held on a not-ready review lets the follower draw level, never
    pass it;
  - a bad `follows` entry is a fault for that route only;
  - routes without `follows` behave exactly as before.
"""
from types import SimpleNamespace
from pytest import raises


def _fake_publisher(name, placing, ok=True):
    p = SimpleNamespace(chart="tQ26.H", placing=placing, updated=False)
    p.publish = lambda: ok
    wm = SimpleNamespace(name=name)
    wm.update = lambda: setattr(p, "updated", True)
    p.watermark = wm
    return p


def _sweep(monkeypatch, marks, publishers, not_ready=()):
    """Run one sweep over `marks` ({name: (placing, follows)}) with the given
    fake publishers. Routes named in `not_ready` raise ReviewNotReady."""
    import dynamicalsystem.gazette as gazette
    from dynamicalsystem.gazette.content import ReviewNotReady

    def fake_watermark(name):
        placing, follows = marks[name]
        return SimpleNamespace(
            name=name, chart="tQ26.H", placing=placing, follows=follows
        )

    def fake_create(watermark, live=False):
        if watermark in not_ready:
            raise ReviewNotReady("not written yet")
        return publishers[watermark]

    alerts = []
    monkeypatch.setattr(gazette, "watermarks", lambda: list(marks))
    monkeypatch.setattr(gazette, "Watermark", fake_watermark)
    monkeypatch.setattr(gazette, "create_publisher", fake_create)
    monkeypatch.setattr(gazette, "send_alert", lambda msg: alerts.append(msg))
    monkeypatch.setattr(
        gazette,
        "PublishGuard",
        lambda: SimpleNamespace(is_published=lambda *a: False, record=lambda *a: None),
    )
    rc = gazette.publish_once()
    return rc, alerts


def test_level_follower_holds_while_leader_goes_ahead(monkeypatch):
    """Leader and follower level at 33, review written: only the leader
    publishes. The run is clean and quiet."""
    abyss = _fake_publisher("abyss", 33)
    josh = _fake_publisher("josh", 33)
    rc, alerts = _sweep(
        monkeypatch,
        {"abyss": (33, ""), "josh": (33, "abyss")},
        {"abyss": abyss, "josh": josh},
    )
    assert rc == 0 and alerts == []
    assert abyss.updated is True
    assert josh.updated is False


def test_follower_one_behind_publishes_with_leader(monkeypatch):
    """Follower at 34, leader at 33 (leader posted 34 yesterday): both publish."""
    abyss = _fake_publisher("abyss", 33)
    josh = _fake_publisher("josh", 34)
    rc, _ = _sweep(
        monkeypatch,
        {"abyss": (33, ""), "josh": (34, "abyss")},
        {"abyss": abyss, "josh": josh},
    )
    assert rc == 0
    assert abyss.updated is True and josh.updated is True


def test_file_order_cannot_let_follower_ride_leader_advance(monkeypatch):
    """Follower listed BEFORE the leader in the file, both level: the follower
    still holds, because it is compared against the leader's start placing."""
    abyss = _fake_publisher("abyss", 33)
    josh = _fake_publisher("josh", 33)
    _sweep(
        monkeypatch,
        {"josh": (33, "abyss"), "abyss": (33, "")},
        {"abyss": abyss, "josh": josh},
    )
    assert abyss.updated is True and josh.updated is False


def test_leader_held_lets_follower_draw_level_then_wait_a_turn(monkeypatch):
    """Day 1: leader held on a not-ready 33, follower at 34 publishes and draws
    level. Day 2: review 33 written, leader publishes, follower holds.
    Day 3: follower publishes 33."""
    # day 1
    abyss = _fake_publisher("abyss", 33)
    josh = _fake_publisher("josh", 34)
    rc, alerts = _sweep(
        monkeypatch,
        {"abyss": (33, ""), "josh": (34, "abyss")},
        {"abyss": abyss, "josh": josh},
        not_ready=("abyss",),
    )
    assert rc == 0 and alerts == []
    assert abyss.updated is False and josh.updated is True  # level at 33
    # day 2
    abyss = _fake_publisher("abyss", 33)
    josh = _fake_publisher("josh", 33)
    _sweep(
        monkeypatch,
        {"abyss": (33, ""), "josh": (33, "abyss")},
        {"abyss": abyss, "josh": josh},
    )
    assert abyss.updated is True and josh.updated is False  # lead restored
    # day 3
    abyss = _fake_publisher("abyss", 32)
    josh = _fake_publisher("josh", 33)
    _sweep(
        monkeypatch,
        {"abyss": (32, ""), "josh": (33, "abyss")},
        {"abyss": abyss, "josh": josh},
    )
    assert abyss.updated is True and josh.updated is True


def test_routes_without_follows_are_unchanged(monkeypatch):
    """No `follows` anywhere: every route publishes independently, as before."""
    a = _fake_publisher("a", 36)
    b = _fake_publisher("b", 33)
    rc, _ = _sweep(monkeypatch, {"a": (36, ""), "b": (33, "")}, {"a": a, "b": b})
    assert rc == 0 and a.updated and b.updated


def test_follows_missing_leader_is_a_fault_for_that_route_only(monkeypatch):
    """A follower whose leader failed to load (no start placing) holds as a
    fault-free wait; a RouteInvalid from Watermark() is a fault that alerts,
    and the other routes still sweep."""
    import dynamicalsystem.gazette as gazette
    from dynamicalsystem.gazette.watermarks import RouteInvalid

    good = _fake_publisher("good", 36)

    def fake_watermark(name):
        if name == "bad":
            raise RouteInvalid("Route bad follows 'ghost', which does not exist.")
        return SimpleNamespace(name=name, chart="tQ26.H", placing=36, follows="")

    alerts = []
    monkeypatch.setattr(gazette, "watermarks", lambda: ["bad", "good"])
    monkeypatch.setattr(gazette, "Watermark", fake_watermark)
    monkeypatch.setattr(gazette, "create_publisher", lambda watermark, live=False: good)
    monkeypatch.setattr(gazette, "send_alert", lambda msg: alerts.append(msg))
    monkeypatch.setattr(
        gazette,
        "PublishGuard",
        lambda: SimpleNamespace(is_published=lambda *a: False, record=lambda *a: None),
    )
    rc = gazette.publish_once()
    assert rc == 1
    assert good.updated is True
    assert len(alerts) == 1 and "bad" in alerts[0] and "ghost" in alerts[0]


# --- leader_of: validation of the follows entry against the loaded file ----


def _marks(**routes):
    return {
        name: {"chart": chart, "placing": 33, "follows": follows}
        for name, (chart, follows) in routes.items()
    }


def test_leader_of_returns_leader_or_empty():
    from dynamicalsystem.gazette.watermarks import leader_of

    m = _marks(abyss=("tQ26.H", ""), josh=("tQ26.H", "abyss"))
    assert leader_of("josh", m) == "abyss"
    assert leader_of("abyss", m) == ""


def test_leader_of_rejects_missing_other_chart_self_and_cycle():
    from dynamicalsystem.gazette.watermarks import RouteInvalid, leader_of

    with raises(RouteInvalid, match="does not exist"):
        leader_of("josh", _marks(josh=("tQ26.H", "ghost")))
    with raises(RouteInvalid, match="different charts"):
        leader_of("josh", _marks(abyss=("tQ25.H", ""), josh=("tQ26.H", "abyss")))
    with raises(RouteInvalid, match="cycle"):
        leader_of("josh", _marks(josh=("tQ26.H", "josh")))
    with raises(RouteInvalid, match="cycle"):
        leader_of(
            "josh",
            _marks(abyss=("tQ26.H", "josh"), josh=("tQ26.H", "abyss")),
        )


def test_watermark_loads_follows_from_file(tmp_path, monkeypatch):
    """Watermark() exposes `follows` from the file, validated."""
    from json import dump

    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.config import settings

    settings.cache_clear()
    with open(tmp_path / "watermarks.json", "w") as f:
        dump(
            {
                "abyss": {"publisher": "Signal", "chart": "tQ26.H", "placing": 33, "target": "g"},
                "josh": {"publisher": "Signal", "chart": "tQ26.H", "placing": 33, "target": "n", "follows": "abyss"},
            },
            f,
        )
    from dynamicalsystem.gazette.watermarks import Watermark

    assert Watermark("josh").follows == "abyss"
    assert Watermark("abyss").follows == ""
    settings.cache_clear()
