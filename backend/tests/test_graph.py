from datetime import datetime, timezone
from pathlib import Path

from deadlock_detector.graph import DependencyGraph
from deadlock_detector.ingest.jira_mock import MockJiraIngestor

DATA = Path(__file__).resolve().parents[1] / "data" / "mock_jira.json"


def _graph():
    return DependencyGraph(MockJiraIngestor(DATA).fetch())


def test_blast_radius_is_seven():
    # The slide's promise: one silent client ticket blocks 7 downstream.
    assert len(_graph().blast_radius("CLIENT-204")) == 7


def test_main_chain_follows_heaviest_branch():
    assert _graph().main_chain("CLIENT-204") == ["CLIENT-204", "TEAMB-88", "TEAMA-42"]


def test_leaf_has_empty_blast_radius():
    assert _graph().blast_radius("QA-15") == set()
