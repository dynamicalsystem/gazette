"""The web adapter: a long-lived FastAPI service over the gazette library.

Ships only `/health` for now (the quadlet's liveness signal in loop 07). Feature
endpoints -- historic reviews, insights, festers -- are a separate arc. This
module does NOT import or trigger the publish sweep: serving and publishing are
independent adapters over the same library.
"""
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.log import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"gazette serve starting (version {version('dynamicalsystem.gazette')})")
    yield
    logger.info("gazette serve stopping")


app = FastAPI(title="gazette", lifespan=lifespan)


@app.get("/health")
def health():
    """Liveness only -- deliberately independent of watermark state, content
    fetch, and publish success, so the health gate reflects the web server, not
    the last publish."""
    return {"status": "ok", "version": version("dynamicalsystem.gazette")}


def serve() -> int:
    """Run the uvicorn server. Called by `gazette serve`."""
    import uvicorn

    config = settings()
    uvicorn.run(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level=config.log_level.lower(),
    )
    return 0
