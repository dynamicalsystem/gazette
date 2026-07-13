loop: 02-signal-http-client
closed: 2026-06-26
outcome: met -- Signal is an HTTP client of the standalone service; prod<->dev is a SIGNAL_URL change

Key result: .env.example + .gitignore added; fixed the broken 400 drain/retry path
(_drain_inbox) and the url_join trailing-slash wart; 5 new mocked unit tests green.
Outcomes O1-O4 met (see README).
Successors: 04 (config delivery), 07 (prod SIGNAL_URL wiring).
