from __future__ import annotations

from dataclasses import dataclass

from agents.models import parse_layout_spec


@dataclass(frozen=True)
class AppendAgentPlan:
    agent: str
    direction: str


def rightmost_leaf_append_plan(old_window, new_window) -> tuple[AppendAgentPlan, ...] | None:
    try:
        old_layout = parse_layout_spec(getattr(old_window, 'user_layout', ''))
        new_layout = parse_layout_spec(getattr(new_window, 'user_layout', ''))
    except Exception:
        return None
    return _rightmost_leaf_append_plan_for_nodes(old_layout, new_layout)


def _rightmost_leaf_append_plan_for_nodes(old_node, new_node) -> tuple[AppendAgentPlan, ...] | None:
    if old_node.kind == 'leaf':
        return _expanded_leaf_append_plan(old_node, new_node)
    if old_node.kind != new_node.kind:
        return None
    assert old_node.left is not None
    assert old_node.right is not None
    assert new_node.left is not None
    assert new_node.right is not None
    if old_node.left.render() != new_node.left.render():
        return None
    return _rightmost_leaf_append_plan_for_nodes(old_node.right, new_node.right)


def _expanded_leaf_append_plan(anchor_node, new_node) -> tuple[AppendAgentPlan, ...] | None:
    if new_node.kind == 'leaf':
        return () if new_node.render() == anchor_node.render() else None
    assert new_node.left is not None
    assert new_node.right is not None
    left_plan = _expanded_leaf_append_plan(anchor_node, new_node.left)
    if left_plan is None:
        return None
    if new_node.right.kind != 'leaf':
        return None
    assert new_node.right.leaf is not None
    direction = 'right' if new_node.kind == 'horizontal' else 'bottom'
    return (*left_plan, AppendAgentPlan(agent=new_node.right.leaf.name, direction=direction))


__all__ = ['AppendAgentPlan', 'rightmost_leaf_append_plan']
