from dynamicalsystem.pytests.environment import variables as environment_variables


def test_gazette(environment_variables):
    assert 1 == 1


def test_cli_publish_defaults_to_dry_run(environment_variables, monkeypatch):
    """`gazette publish` invokes publish_once(live=False)."""
    from dynamicalsystem.gazette.cli import cli

    calls = []
    monkeypatch.setattr(
        "dynamicalsystem.gazette.cli.publish_once", lambda live=False: calls.append(live) or 0
    )

    rc = cli(["publish"])

    assert rc == 0
    assert calls == [False]


def test_cli_publish_live_passes_true(environment_variables, monkeypatch):
    """`gazette publish --live` invokes publish_once(live=True)."""
    from dynamicalsystem.gazette.cli import cli

    calls = []
    monkeypatch.setattr(
        "dynamicalsystem.gazette.cli.publish_once", lambda live=False: calls.append(live) or 0
    )

    rc = cli(["publish", "--live"])

    assert rc == 0
    assert calls == [True]
