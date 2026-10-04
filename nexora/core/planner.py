"""Heuristic planner: decomposes a goal into executable steps.

A model-driven planner (via the Model Bus) replaces this when a provider is
configured; the heuristic keeps Nexora fully functional in local-only mode
with no model installed.
"""
import re


class Planner:
    def plan(self, goal: str) -> list[dict]:
        goal = (goal or "").strip()
        if not goal:
            return []
        steps: list[dict] = [{"id": 1, "kind": "analyze", "description": f"Understand goal: {goal}"}]
        g = goal.lower()
        if any(w in g for w in ("file", "folder", "directory", "workspace")):
            steps.append({"id": 2, "kind": "tool", "tool": "filesystem",
                          "action": "list", "description": "Inspect relevant files"})
        if any(w in g for w in ("search", "research", "find", "monitor", "news")):
            steps.append({"id": len(steps) + 1, "kind": "tool", "tool": "http",
                          "action": "search", "description": "Gather sources"})
        if re.search(r"\b(code|implement|build|script|function|fix)\b", g):
            steps.append({"id": len(steps) + 1, "kind": "work",
                          "description": "Produce implementation in the Dot workspace"})
        steps.append({"id": len(steps) + 1, "kind": "summarize",
                      "description": "Summarize outcome and store memory"})
        return steps
