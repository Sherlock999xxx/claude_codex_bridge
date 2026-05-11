from __future__ import annotations

from provider_backends.codex.start_cmd_runtime.fields import (
    effective_start_cmd,
    persist_resume_start_cmd_fields,
    resume_template_command,
)


def test_effective_start_cmd_rebuilds_resume_from_base_start_command() -> None:
    data = {
        "start_cmd": "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true",
        "codex_start_cmd": "codex resume stale-session",
        "codex_session_id": "fresh-session",
    }

    assert effective_start_cmd(data) == (
        "export CODEX_RUNTIME_DIR=/tmp/demo; "
        "codex -c disable_paste_burst=true resume fresh-session"
    )


def test_persist_resume_start_cmd_fields_updates_both_stored_fields() -> None:
    data = {
        "start_cmd": "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true",
    }

    updated = persist_resume_start_cmd_fields(data, "resume-session")

    assert updated == (
        "export CODEX_RUNTIME_DIR=/tmp/demo; "
        "codex -c disable_paste_burst=true resume resume-session"
    )
    assert data["codex_start_cmd"] == updated
    assert data["start_cmd"] == updated


def test_resume_template_command_prefers_non_resume_base_command() -> None:
    data = {
        "start_cmd": "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true",
        "codex_start_cmd": "codex resume stale-session",
    }

    assert resume_template_command(data) == "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true"


def test_effective_start_cmd_strips_bare_resume_without_session_id() -> None:
    data = {
        "codex_start_cmd": "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true resume",
    }

    assert effective_start_cmd(data) == "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true"


def test_effective_start_cmd_falls_back_to_base_when_codex_resume_is_unusable() -> None:
    data = {
        "start_cmd": "codex --model gpt-5.4",
        "codex_start_cmd": "codex resume",
    }

    assert effective_start_cmd(data) == "codex --model gpt-5.4"


def test_effective_start_cmd_rebuilds_resume_when_stored_resume_has_no_id() -> None:
    data = {
        "start_cmd": "export CODEX_RUNTIME_DIR=/tmp/demo; codex -c disable_paste_burst=true",
        "codex_start_cmd": "codex resume",
        "codex_session_id": "fresh-session",
    }

    assert effective_start_cmd(data) == (
        "export CODEX_RUNTIME_DIR=/tmp/demo; "
        "codex -c disable_paste_burst=true resume fresh-session"
    )
