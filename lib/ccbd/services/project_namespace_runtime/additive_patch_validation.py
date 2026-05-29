from __future__ import annotations

from collections.abc import Mapping

from ccbd.reload_additive_agents import append_agent_windows, new_agent_targets, window_map


def unsupported_additive_patch_reason(
    patch_plan: dict[str, object],
    old_topology,
    new_topology,
) -> tuple[str, str] | None:
    reason = _patch_plan_status_reason(patch_plan)
    if reason is not None:
        return reason
    old_windows = set(window_map(old_topology))
    new_windows = set(window_map(new_topology))
    if old_windows - new_windows:
        return ('unsupported_topology_change', 'namespace additive patch cannot remove windows')
    append_windows = append_agent_windows(old_topology, new_topology)
    if append_windows is None:
        return ('non_append_agent_layout', 'namespace additive patch only supports appending agents at the end of an existing window')
    added_windows = new_windows - old_windows
    steps = _patch_steps(patch_plan)
    expected_new_agents = new_agent_targets(old_topology, new_topology)
    reason = _planned_target_reason(steps, added_windows, append_windows, expected_new_agents)
    if reason is not None:
        return reason
    return _step_proof_reason(steps, added_windows, append_windows, expected_new_agents)


def _patch_plan_status_reason(patch_plan: dict[str, object]) -> tuple[str, str] | None:
    if str((patch_plan or {}).get('status') or '') != 'planned':
        return ('patch_plan_not_planned', 'namespace patch plan is not planned')
    if tuple((patch_plan or {}).get('blocked_operations') or ()):
        return ('patch_plan_blocked', 'namespace patch plan has blocked operations')
    return None


def _patch_steps(patch_plan: dict[str, object]) -> tuple[Mapping[str, object] | object, ...]:
    return tuple((patch_plan or {}).get('steps') or ())


def _planned_target_reason(
    steps: tuple[Mapping[str, object] | object, ...],
    added_windows: set[str],
    append_windows: dict[str, object],
    expected_new_agents: set[tuple[str, str]],
) -> tuple[str, str] | None:
    planned_windows = _planned_create_windows(steps)
    if planned_windows != added_windows:
        return ('patch_plan_mismatch', 'namespace patch plan windows do not match new topology windows')
    if _planned_agent_targets(steps) != expected_new_agents:
        return ('patch_plan_mismatch', 'namespace patch plan agent panes do not match new topology agents')
    if not planned_windows and not append_windows:
        return ('unsupported_patch_step', 'namespace additive patch has no supported namespace mutation steps')
    return None


def _planned_create_windows(steps: tuple[Mapping[str, object] | object, ...]) -> set[str]:
    return {
        str(step.get('window') or '')
        for step in steps
        if isinstance(step, Mapping) and step.get('action') == 'create_window'
    }


def _planned_agent_targets(steps: tuple[Mapping[str, object] | object, ...]) -> set[tuple[str, str]]:
    return {
        (str(step.get('window') or ''), str(step.get('agent') or ''))
        for step in steps
        if isinstance(step, Mapping) and step.get('action') == 'create_agent_pane'
    }


def _step_proof_reason(
    steps: tuple[Mapping[str, object] | object, ...],
    added_windows: set[str],
    append_windows: dict[str, object],
    expected_new_agents: set[tuple[str, str]],
) -> tuple[str, str] | None:
    for step in steps:
        reason = _single_step_reason(step, added_windows, append_windows, expected_new_agents)
        if reason is not None:
            return reason
    return None


def _single_step_reason(
    step: Mapping[str, object] | object,
    added_windows: set[str],
    append_windows: dict[str, object],
    expected_new_agents: set[tuple[str, str]],
) -> tuple[str, str] | None:
    if not isinstance(step, Mapping):
        return ('invalid_patch_step', 'namespace patch plan step must be an object')
    action = str(step.get('action') or '')
    window = str(step.get('window') or '')
    if action == 'refresh_project_view':
        return None
    if action not in {'create_window', 'create_sidebar_pane', 'create_agent_pane'}:
        return ('unsupported_patch_step', f'unsupported namespace patch step: {action}')
    reason = _step_scope_reason(action, window, step, added_windows, append_windows, expected_new_agents)
    if reason is not None:
        return reason
    return _step_identity_reason(action, step)


def _step_scope_reason(
    action: str,
    window: str,
    step: Mapping[str, object],
    added_windows: set[str],
    append_windows: dict[str, object],
    expected_new_agents: set[tuple[str, str]],
) -> tuple[str, str] | None:
    if action in {'create_window', 'create_sidebar_pane'} and window not in added_windows:
        return ('unsupported_patch_step', 'window/sidebar patch steps are only supported for newly-added windows')
    if action != 'create_agent_pane':
        return None
    if window not in added_windows and window not in append_windows:
        return ('patch_plan_mismatch', 'agent pane patch step window is not an added window or append-only existing window')
    if (window, str(step.get('agent') or '')) not in expected_new_agents:
        return ('patch_plan_mismatch', 'agent pane patch step does not match a new topology agent')
    return None


def _step_identity_reason(action: str, step: Mapping[str, object]) -> tuple[str, str] | None:
    if str(step.get('managed_by') or '') != 'ccbd':
        return ('scope_proof_missing', 'namespace patch step is missing managed_by=ccbd proof')
    if action not in {'create_sidebar_pane', 'create_agent_pane'}:
        return None
    role = str(step.get('role') or '')
    slot_key = str(step.get('slot_key') or '')
    if not role or not slot_key:
        return ('scope_proof_missing', 'namespace patch pane step is missing role or slot_key proof')
    expected_role = 'sidebar' if action == 'create_sidebar_pane' else 'agent'
    if role != expected_role:
        return ('scope_proof_mismatch', f'namespace patch pane step role must be {expected_role}')
    return None


__all__ = ['unsupported_additive_patch_reason']
