"""Stage 1 + 3: in-memory dependency graph and blast-radius BFS.

A team's dependency graph is small (hundreds of nodes), so an in-memory
adjacency list + BFS computes blast radius instantly — no graph DB needed for
the MVP. Edges encode "X is blocked by Y" (Jira's `is blocked by` link); the
blast radius of a stalled node is everything transitively downstream of it.
"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

from .models import Ticket


class DependencyGraph:
    def __init__(self, tickets: list[Ticket]):
        self.tickets: dict[str, Ticket] = {t.key: t for t in tickets}
        # downstream[Y] = set of tickets that Y blocks (i.e. wait on Y)
        self._downstream: dict[str, set[str]] = defaultdict(set)
        for t in tickets:
            for upstream in t.blocked_by:
                self._downstream[upstream].add(t.key)

    def directly_blocks(self, key: str) -> set[str]:
        return set(self._downstream.get(key, ()))

    def blast_radius(self, key: str) -> set[str]:
        """All tickets transitively blocked by `key` (excludes `key` itself)."""
        seen: set[str] = set()
        queue = deque(self._downstream.get(key, ()))
        while queue:
            node = queue.popleft()
            if node in seen:
                continue
            seen.add(node)
            queue.extend(self._downstream.get(node, set()) - seen)
        return seen

    def affected_teams(self, keys: Iterable[str]) -> set[str]:
        """Derive team from the ticket-key prefix, e.g. TEAMA-42 -> TEAMA."""
        return {k.split("-")[0] for k in keys}

    def main_chain(self, root: str, max_len: int = 3) -> list[str]:
        """Representative downstream path, following the heaviest branch."""
        chain = [root]
        cur = root
        while len(chain) < max_len:
            nxt = self.directly_blocks(cur)
            if not nxt:
                break
            cur = max(nxt, key=lambda k: (len(self.blast_radius(k)), k))
            chain.append(cur)
        return chain
