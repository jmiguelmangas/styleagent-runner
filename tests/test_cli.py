import pytest

from runner.cli import build_parser, main


def test_parser_program_name() -> None:
    parser = build_parser()
    assert parser.prog == "styleagent-runner"


def test_main_help_outputs_usage(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "usage: styleagent-runner" in captured.out


def test_parser_supports_poll_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["poll", "--once"])
    assert args.command == "poll"
    assert args.once is True
