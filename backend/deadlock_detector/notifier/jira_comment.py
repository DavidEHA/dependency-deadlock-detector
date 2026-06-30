"""Production delivery: post a comment + @mention on the stalled ticket.

Primary channel for production because it uses Jira access the team already has
— zero new permission gates (corporate Teams admin is locked). Stubbed here:
wiring the Jira REST call is a later step once credentials are available.
"""
from __future__ import annotations

from ..models import Ticket


class JiraCommentNotifier:
    name = "jira-comment"

    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = base_url
        self.token = token

    def send(self, ticket: Ticket, message: str) -> None:
        if not (self.base_url and self.token):
            raise RuntimeError(
                "Jira not configured — set JIRA_BASE_URL and JIRA_TOKEN."
            )
        # TODO: POST {base_url}/rest/api/3/issue/{ticket.key}/comment
        #       with an ADF body that @mentions ticket.owner.handle.
        raise NotImplementedError("Jira REST delivery not wired yet.")
