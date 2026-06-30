from __future__ import annotations

from typing import Protocol

from ..models import Ticket


class Ingestor(Protocol):
    def fetch(self) -> list[Ticket]: ...
