from __future__ import annotations

from typing import Protocol

from ..models import Ticket


class Notifier(Protocol):
    name: str

    def send(self, ticket: Ticket, message: str) -> None: ...
