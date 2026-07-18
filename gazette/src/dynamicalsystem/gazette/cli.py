"""gazette command line: two thin adapters over the library core.

    gazette publish [--live]   -- run one publish sweep and exit (batch / timer / tests)
    gazette serve              -- run the long-lived FastAPI + uvicorn web service

`publish` defaults to Validator/dry-run. Live publishers are enabled only with
`--live` AND `GAZETTE_LIVE=1` in the environment. `serve` does not publish and
has no opt-in.

`publish` calls the library directly and never imports the web stack; `serve`'s
imports are deferred into its branch so the batch path stays web-free.
"""
import argparse
from importlib.metadata import version

from dynamicalsystem.gazette import publish_once


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gazette", description=__doc__)
    parser.add_argument(
        "--version",
        action="version",
        version=version("dynamicalsystem.gazette"),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    publish_parser = sub.add_parser("publish", help="run one publish sweep and exit")
    publish_parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="use real publishers (requires GAZETTE_LIVE=1)",
    )
    sub.add_parser("serve", help="run the long-lived web service")

    args = parser.parse_args(argv)

    if args.command == "publish":
        return publish_once(live=args.live)

    if args.command == "serve":
        # deferred import: keeps fastapi/uvicorn out of the publish path
        from dynamicalsystem.gazette.app import serve

        return serve()

    return 2
