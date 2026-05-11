from __future__ import annotations

from provider_backends.codex.start_cmd_runtime.parsing import (
    extract_resume_session_id,
    looks_like_bare_resume_cmd,
    resume_command_missing_session_id,
)
from provider_backends.codex.start_cmd_runtime.rewriting import build_resume_start_cmd, strip_resume_start_cmd


def test_extract_resume_session_id_prefers_regex_match() -> None:
    command = 'export X=1; codex -c disable_paste_burst=true resume sess-123'

    assert extract_resume_session_id(command) == 'sess-123'


def test_extract_resume_session_id_falls_back_to_token_scan() -> None:
    command = '/usr/local/bin/codex resume sess-456'

    assert extract_resume_session_id(command) == 'sess-456'


def test_extract_resume_session_id_rejects_invalid_shell_syntax() -> None:
    command = 'codex "unterminated'

    assert extract_resume_session_id(command) is None


def test_looks_like_bare_resume_cmd_accepts_simple_resume() -> None:
    assert looks_like_bare_resume_cmd('/usr/local/bin/codex resume sess-789') is True


def test_looks_like_bare_resume_cmd_rejects_shell_wrapped_command() -> None:
    assert looks_like_bare_resume_cmd('export CODEX_HOME=/tmp; codex resume sess-789') is False


def test_strip_resume_start_cmd_removes_resume_suffix_from_shell_wrapped_command() -> None:
    command = 'export CODEX_HOME=/tmp/home CODEX_SESSION_ROOT=/tmp/home/sessions; codex -m gpt-5.4 resume sess-789'

    assert strip_resume_start_cmd(command) == (
        'export CODEX_HOME=/tmp/home CODEX_SESSION_ROOT=/tmp/home/sessions; '
        'codex -m gpt-5.4'
    )


def test_resume_command_missing_session_id_detects_bare_resume_without_id() -> None:
    assert resume_command_missing_session_id('codex resume') is True
    assert resume_command_missing_session_id('export CODEX_HOME=/tmp/home; codex -m gpt-5.4 resume') is True
    assert resume_command_missing_session_id('codex resume sess-789') is False


def test_build_resume_start_cmd_strips_bare_resume_when_session_id_is_empty() -> None:
    command = 'export CODEX_HOME=/tmp/home; codex -m gpt-5.4 resume'

    assert build_resume_start_cmd(command, '') == 'export CODEX_HOME=/tmp/home; codex -m gpt-5.4'
