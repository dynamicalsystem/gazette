from dynamicalsystem.pytests.environment import variables as environment_variables
from json import dump, load
from os.path import join, exists
from os import environ


def test_watermark_file_exists(environment_variables):
    from dynamicalsystem.gazette.watermarks import Watermark
    
    _ = Watermark("signal_to_abyss")
    _.logger.info(f'Environment is \'{environ.get("DYNAMICALSYSTEM_ENVIRONMENT", "unknown")}\'')
    
    assert exists(_.watermark_file), f"Watermark file '{_.watermark_file}' does not exist"


def test_get_watermarks(environment_variables):
    from dynamicalsystem.gazette.watermarks import watermarks

    _ = watermarks()
    assert "example_signal_route" in _
    assert "example_bluesky_route" in _


def test_watermark_update_creates_backup_and_log(tmp_path, environment_variables):
    """Watermark.update() snapshots the file and appends an audit log entry."""
    from dynamicalsystem.gazette.watermarks import Watermark

    watermark_file = tmp_path / "watermarks.json"
    dump(
        {
            "test_target": {
                "publisher": "Validator",
                "chart": "tQ26.H",
                "placing": 97,
                "target": "dev",
            }
        },
        watermark_file.open("w"),
        indent=4,
    )

    wm = Watermark("test_target")
    wm.watermark_file = str(watermark_file)
    wm._load()
    assert wm.placing == 97

    wm.update()

    backup_file = tmp_path / "watermarks.json.bak"
    log_file = tmp_path / "watermarks.json.log"

    assert backup_file.exists(), "backup file should be created"
    assert log_file.exists(), "audit log file should be created"

    restored = load(backup_file.open())
    assert restored["test_target"]["placing"] == 97

    current = load(watermark_file.open())
    assert current["test_target"]["placing"] == 96

    log_lines = log_file.read_text().strip().splitlines()
    assert len(log_lines) == 1
    assert "watermark=test_target" in log_lines[0]
    assert "old=tQ26.H.97" in log_lines[0]
    assert "new=tQ26.H.96" in log_lines[0]

