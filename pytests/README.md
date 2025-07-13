# pytests for dynamicalsystem.gazette

## Prerequisites

`~/.local/share/<namespace>/config/gazette.pytest.env` must contain values for:
- `CONTENT_GITHUB_TOKEN` - Your fine grained access token to the content repo on github
- `CONTENT_GITHUB_URL` - url to the raw repo, i.e. `https://raw.githubusercontent.com/<namespace>/content/main/`

## Operation

`make test` will run the tests.