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
    from dynamicalsystem.gazette.content import GitHub

    content = GitHub("nothing", 100)
    assert not bool(content.item)

def test_github_content_is_missing(environment_variables):
    from dynamicalsystem.gazette.content import GitHub

    with raises(IndexError) as e:
        _ = GitHub("test", 101)
        assert e.value == "No review found for item 101 in series test."
