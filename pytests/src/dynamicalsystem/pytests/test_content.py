from dynamicalsystem.pytests.environment import variables as environment_variables
from pytest import raises


def test_github_is_valid(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 100)
    assert content.validate_content()

def test_github_review_key_is_missing(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 98)
    assert not content.validate_content()

def test_github_review_value_is_empty(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 97)
    assert not content.validate_content()

def test_github_verdict_key_is_missing(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 96)
    assert not content.validate_content()

def test_github_verdict_is_bad(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 94)
    assert not content.validate_content()

def test_verdict_value_is_empty(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("test", 95)
    assert not content.validate_content()

def test_github_series_is_missing(environment_variables):
    from dynamicalsystem.gazette.content import GitHub, ChartUnavailable

    # a missing chart file (404) is now a loud fault, not a silent item=None
    with raises(ChartUnavailable):
        GitHub("nothing", 100)

def test_github_content_is_missing(environment_variables):
    from dynamicalsystem.gazette.content import GitHub, ReviewNotReady

    # a placing past the end of the chart is "not written yet", held quietly
    with raises(ReviewNotReady):
        GitHub("test", 101)
