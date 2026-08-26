"""Shared fixture HTML constants for engine tests."""

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
PROGRAM_HTML = (FIXTURES / "program_page.html").read_text(encoding="utf-8")
JS_SHELL_HTML = (FIXTURES / "js_shell.html").read_text(encoding="utf-8")
