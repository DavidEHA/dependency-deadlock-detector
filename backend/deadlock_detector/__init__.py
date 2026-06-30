"""Dependency Deadlock Detector — portable, cloud-agnostic core.

Pipeline: ingest -> graph -> staleness -> blast-radius -> severity -> dedupe
-> draft -> notify. ~80% deterministic code; the LLM touches only the drafting
step. See PROJECT_BRIEF.md for the design rationale.
"""

__version__ = "0.1.0"
