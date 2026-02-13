"""
Poetry script to run the services
"""

import uvicorn
import argparse

from src.config import settings


def api():
    parser = argparse.ArgumentParser(description="Run API server")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run API in local development mode",
    )

    args = parser.parse_args()

    if args.local:
        uvicorn.run(
            "src.main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
        )
    else:
        uvicorn.run(
            "src.main:app",
            host=settings.host,
            port=settings.port,
            workers=settings.workers,
        )
