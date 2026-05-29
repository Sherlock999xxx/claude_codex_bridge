from __future__ import annotations

from ccbd.reload_runtime_mount_state import clean_text, valid_pane_id


def blocked_mount_reason(
    graph,
    namespace,
    agent_panes: dict[str, str],
    preserved_agents: tuple[str, ...],
) -> tuple[str, str] | None:
    if namespace is None:
        return ('namespace_unavailable', 'runtime mounts require current namespace scope')
    reason = _namespace_scope_reason(graph, namespace)
    if reason is not None:
        return reason
    reason = _agent_scope_reason(graph, agent_panes, preserved_agents)
    if reason is not None:
        return reason
    return None


def existing_runtime_agents(
    before_new: dict[str, dict[str, object] | None],
    requested_agents: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(agent for agent in requested_agents if before_new.get(agent) is not None)


def _namespace_scope_reason(graph, namespace) -> tuple[str, str] | None:
    graph_project_id = _graph_project_id(graph)
    namespace_project_id = clean_text(getattr(namespace, 'project_id', None))
    if namespace_project_id and graph_project_id:
        if namespace_project_id != graph_project_id:
            return (
                'namespace_project_mismatch',
                'namespace project_id does not match target service graph',
            )
    if not bool(getattr(namespace, 'ui_attachable', True)):
        return (
            'namespace_not_attachable',
            'runtime mounts require an attachable namespace',
        )
    if not clean_text(getattr(namespace, 'tmux_socket_path', None)):
        return ('namespace_scope_missing', 'namespace tmux socket path is missing')
    if not clean_text(getattr(namespace, 'tmux_session_name', None)):
        return ('namespace_scope_missing', 'namespace tmux session name is missing')
    if getattr(namespace, 'namespace_epoch', None) is None:
        return ('namespace_scope_missing', 'namespace epoch is missing')
    return None


def _agent_scope_reason(
    graph,
    agent_panes: dict[str, str],
    preserved_agents: tuple[str, ...],
) -> tuple[str, str] | None:
    overlap = tuple(sorted(set(agent_panes) & set(preserved_agents)))
    if overlap:
        return (
            'preserved_agent_mount_blocked',
            'runtime mounts cannot target preserved agents: ' + ','.join(overlap),
        )
    missing_panes = tuple(
        sorted(agent for agent, pane in agent_panes.items() if not valid_pane_id(pane))
    )
    if missing_panes:
        return (
            'agent_pane_missing',
            'new agent pane evidence is missing: ' + ','.join(missing_panes),
        )
    unknown = tuple(sorted(set(agent_panes) - _configured_agents(graph)))
    if unknown:
        return (
            'agent_not_configured',
            'new agent is not in target config: ' + ','.join(unknown),
        )
    return None


def _configured_agents(graph) -> set[str]:
    return set(getattr(getattr(graph, 'config', None), 'agents', {}) or {})


def _graph_project_id(graph) -> str | None:
    supervisor = getattr(graph, 'runtime_supervisor', None)
    return clean_text(getattr(supervisor, '_project_id', None))


__all__ = ['blocked_mount_reason', 'existing_runtime_agents']
