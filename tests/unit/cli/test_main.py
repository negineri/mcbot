"""Unit tests for the CLI module."""

import pytest

from mcbot.cli import main


def test_main(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    captured = capsys.readouterr()
    assert "Hello from mcbot!" in captured.out
