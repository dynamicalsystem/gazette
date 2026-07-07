loop: 06-service-skeleton
closed: 2026-07-07
outcome: met -- gazette runs as a long-lived FastAPI service with /health; publish is a sibling one-shot CLI

Key result: publish_once() library fn; cli.py (publish/serve, serve lazy-imported so
publish stays web-free); app.py (FastAPI /health, independent of watermark/content/
network); config http_host/http_port; deps fastapi + uvicorn[standard]; dockerfile
CMD serve (one-shot = `podman run <img> publish`). publish_once guards the loop-03
missing-watermark crash.
Verified: 18 offline tests green (6 new); live publish dry-run (place 98 x4 Validator),
live serve /health 200, container both invocations. Merged 7b4ee3d.
Successors: 07 (tinsnip quadlet + timer + go-live).
