"""Loop 02: vendored url_join joins cleanly with no trailing slash."""
from dynamicalsystem.gazette.utils import url_join, possessive


def test_url_join_no_trailing_slash():
    assert url_join("http://signal:8080", ["v2/send"]) == "http://signal:8080/v2/send"
    assert (
        url_join("http://signal:8080", ["v1/receive", "+100"])
        == "http://signal:8080/v1/receive/+100"
    )


def test_url_join_tolerates_slashes():
    # trailing slash on base, leading/trailing on fragments
    assert (
        url_join("https://host/main/", ["/tQ.json/"]) == "https://host/main/tQ.json"
    )


def test_possessive():
    assert possessive("Bjork") == "Bjork's"
    assert possessive("Boards") == "Boards'"  # already ends in s
