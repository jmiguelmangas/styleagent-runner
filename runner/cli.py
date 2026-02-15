"""CLI entrypoint for StyleAgent runner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


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
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    parser.parse_args(argv)


if __name__ == "__main__":
    main()
