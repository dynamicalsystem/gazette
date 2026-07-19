from datetime import datetime, timezone, timedelta
from json import dump
from os.path import join


def _write_guard(data_folder, data):
    with open(join(data_folder, "published.json"), "w") as f:
        dump(data, f)


def _clear_settings_cache():
    from dynamicalsystem.gazette.config import settings

    settings.cache_clear()


def test_guard_allows_first_publish(tmp_path, monkeypatch):
    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    guard = PublishGuard(window_hours=1)

    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is False


def test_guard_blocks_repeat_within_window(tmp_path, monkeypatch):
    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    _write_guard(
        tmp_path,
        {"calendrical_rot:tQ26.H.88": datetime.now(timezone.utc).isoformat()},
    )

    guard = PublishGuard(window_hours=24)
    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is True


def test_guard_allows_repeat_after_window(tmp_path, monkeypatch):
    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    _write_guard(
        tmp_path,
        {
            "calendrical_rot:tQ26.H.88": (
                datetime.now(timezone.utc) - timedelta(hours=25)
            ).isoformat()
        },
    )

    guard = PublishGuard(window_hours=24)
    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is False


def test_guard_records_publish(tmp_path, monkeypatch):
    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    guard = PublishGuard(window_hours=1)

    guard.record("calendrical_rot", "tQ26.H", 88)

    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is True
    assert guard.is_published("calendrical_rot", "tQ26.H", 87) is False
    assert guard.is_published("abyss", "tQ26.H", 88) is False


def test_guard_tolerates_corrupt_file(tmp_path, monkeypatch):
    """A corrupt guard file fails open (no fault) and is rewritten on record."""
    from json import load

    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    guard_file = tmp_path / "published.json"
    guard_file.write_text("{not json")

    guard = PublishGuard(window_hours=24)
    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is False

    guard.record("calendrical_rot", "tQ26.H", 88)
    with open(guard_file) as f:
        data = load(f)
    assert list(data) == ["calendrical_rot:tQ26.H.88"]


def test_guard_tolerates_non_object_file(tmp_path, monkeypatch):
    """A guard file holding a JSON array is treated as empty."""
    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    (tmp_path / "published.json").write_text("[1, 2, 3]")

    guard = PublishGuard(window_hours=24)
    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is False


def test_guard_record_prunes_expired_and_invalid_entries(tmp_path, monkeypatch):
    """record() drops entries outside the window and unparseable timestamps."""
    from json import load

    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    _write_guard(
        tmp_path,
        {
            "calendrical_rot:tQ26.H.90": (
                datetime.now(timezone.utc) - timedelta(hours=25)
            ).isoformat(),
            "calendrical_rot:tQ26.H.89": "not-a-timestamp",
            "abyss:tQ26.H.88": datetime.now(timezone.utc).isoformat(),
        },
    )

    guard = PublishGuard(window_hours=24)
    guard.record("calendrical_rot", "tQ26.H", 88)

    with open(tmp_path / "published.json") as f:
        data = load(f)
    assert sorted(data) == ["abyss:tQ26.H.88", "calendrical_rot:tQ26.H.88"]


def test_sweep_lock_excludes_second_holder(tmp_path, monkeypatch):
    """A second sweep_lock on the same data folder fails fast."""
    from pytest import raises

    _clear_settings_cache()
    monkeypatch.setenv("DATA_FOLDER", str(tmp_path))
    from dynamicalsystem.gazette.publish_guard import SweepInProgress, sweep_lock

    with sweep_lock():
        with raises(SweepInProgress):
            with sweep_lock():
                pass

    # Released on exit: can be taken again.
    with sweep_lock():
        pass


def test_guard_save_is_atomic_and_creates_folder(tmp_path, monkeypatch):
    """Saving writes via a temp file (no .tmp left behind) and creates the
    data folder if missing."""
    _clear_settings_cache()
    missing = tmp_path / "not" / "yet" / "created"
    monkeypatch.setenv("DATA_FOLDER", str(missing))
    from dynamicalsystem.gazette.publish_guard import PublishGuard

    guard = PublishGuard(window_hours=24)
    guard.record("calendrical_rot", "tQ26.H", 88)

    assert (missing / "published.json").exists()
    assert not (missing / "published.json.tmp").exists()
    assert guard.is_published("calendrical_rot", "tQ26.H", 88) is True
