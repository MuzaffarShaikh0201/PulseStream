"""
Poetry script to run the services
"""

import sys
import uvicorn
import argparse
import subprocess

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
            host="localhost",
            port=settings.port,
            reload=True,
        )
    else:
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=settings.port,
            workers=settings.workers,
        )


def worker():
    parser = argparse.ArgumentParser(description="Run background workers")

    parser.add_argument(
        "--base",
        action="store_true",
        help="Run base worker",
    )
    parser.add_argument(
        "--aggregator",
        action="store_true",
        help="Run aggregator worker",
    )

    args = parser.parse_args()

    if not args.base and not args.aggregator:
        print(
            "\n❌ No worker specified.\n\n"
            "Please run ONE worker per command.\n\n"
            "Examples:\n"
            "  poetry run worker --base\n"
            "  poetry run worker --aggregator\n\n"
            "To run multiple workers, open separate terminals or sessions.\n"
        )
        return

    if args.base and args.aggregator:
        print(
            "\n❌ Multiple workers specified in one command.\n\n"
            "Please run only ONE worker per command.\n\n"
            "Example:\n"
            "  poetry run worker --base\n\n"
            "To run multiple workers, use separate terminals or sessions.\n"
        )
        return

    module = "src.workers.base_worker" if args.base else "src.workers.aggregator"

    subprocess.run(
        [sys.executable, "-m", module],
        check=True,
    )
