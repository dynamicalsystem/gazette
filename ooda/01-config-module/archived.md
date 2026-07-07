loop: 01-config-module
closed: 2026-06-26
outcome: met -- gazette resolves config and logs with no halogen import

Key result: config.py (pydantic-settings flat Settings), log.py (stdout-only),
utils.py (vendored url_join/possessive/cli_hyperlink); halogen removed from
pyproject and all call sites rewired; 3 new config tests green.
Outcomes O1-O4 met (see README).
Successors: 02-signal-http-client, 03-build-from-source.
