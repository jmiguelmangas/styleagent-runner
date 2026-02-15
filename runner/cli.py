"""CLI entrypoint for StyleAgent runner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from runner.api import RunnerBackendApi
from runner.config import RunnerSettings
from runner.http import RunnerHttpClient
from runner.jobs import JobExecutor
from runner.poller import RunnerPoller


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="styleagent-runner",
        description="StyleAgent runner CLI (MVP thin worker).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="styleagent-runner 0.1.0",
    )
    subparsers = parser.add_subparsers(dest="command")
    poll_parser = subparsers.add_parser("poll", help="Poll backend for pending jobs")
    poll_parser.add_argument(
        "--once",
        action="store_true",
        help="Run one polling iteration and exit",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "poll":
        settings = RunnerSettings.from_env()
        with RunnerHttpClient(settings) as client:
            api = RunnerBackendApi(client)
            executor = JobExecutor(client)
            poller = RunnerPoller(
                api,
                executor,
                poll_interval_seconds=settings.poll_interval_seconds,
            )
            if args.once:
                poller.poll_once()
            else:
                poller.poll_forever()


if __name__ == "__main__":
    main()
