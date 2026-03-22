"""Unit tests for executive summary mode."""
import pytest
from unittest.mock import AsyncMock, patch

from deliberation.summarizer import DeliberationSummarizer
from models.schema import Summary, RoundResponse


class TestExecutiveSummaryPrompt:
    """Tests for executive summary prompt generation."""

    def test_executive_summary_prompt_is_plain_english(self):
        """Verify the prompt asks for non-technical language."""
        from adapters.base import BaseCLIAdapter

        class FakeAdapter(BaseCLIAdapter):
            def parse_output(self, raw_output):
                return raw_output

        adapter = FakeAdapter(command="fake", args=[])
        summarizer = DeliberationSummarizer(adapter, "test-model")

        summary = Summary(
            consensus="The code has security issues",
            key_agreements=["Input validation is missing"],
            key_disagreements=["Severity is debated"],
            final_recommendation="Fix validation before launch",
        )

        prompt = summarizer._create_executive_summary_prompt(
            "Review the auth system", summary
        )

        assert "non-technical" in prompt.lower()
        assert "no code" in prompt.lower()
        assert "no jargon" in prompt.lower()
        assert "3" in prompt  # 3 paragraphs
        assert "business" in prompt.lower()

    def test_executive_summary_prompt_includes_findings(self):
        """Verify prompt includes the actual findings."""
        from adapters.base import BaseCLIAdapter

        class FakeAdapter(BaseCLIAdapter):
            def parse_output(self, raw_output):
                return raw_output

        adapter = FakeAdapter(command="fake", args=[])
        summarizer = DeliberationSummarizer(adapter, "test-model")

        summary = Summary(
            consensus="Database queries are slow",
            key_agreements=["Need indexes", "Need caching"],
            key_disagreements=["Redis vs Memcached"],
            final_recommendation="Add indexes first",
        )

        prompt = summarizer._create_executive_summary_prompt(
            "Performance review", summary
        )

        assert "Database queries are slow" in prompt
        assert "Need indexes" in prompt
        assert "Add indexes first" in prompt


class TestSummarySchema:
    """Tests for Summary schema with executive_summary field."""

    def test_executive_summary_is_optional(self):
        """Executive summary should be optional (backward compat)."""
        summary = Summary(
            consensus="Test",
            key_agreements=["a"],
            key_disagreements=["b"],
            final_recommendation="c",
        )
        assert summary.executive_summary is None

    def test_executive_summary_can_be_set(self):
        """Executive summary can be provided."""
        summary = Summary(
            consensus="Test",
            key_agreements=["a"],
            key_disagreements=["b"],
            final_recommendation="c",
            executive_summary="Your site looks good. One small issue with forms. Fix it before launch.",
        )
        assert "forms" in summary.executive_summary


class TestPanelPresets:
    """Tests for pre-commit review panels."""

    def test_panels_yaml_has_pre_commit_review(self):
        """Verify pre-commit-review panel exists in panels.yaml."""
        import yaml
        from pathlib import Path

        panels_path = Path(__file__).parent.parent.parent / "panels.yaml"
        with open(panels_path) as f:
            data = yaml.safe_load(f)

        panels = data["panels"]
        assert "pre-commit-review" in panels
        panel = panels["pre-commit-review"]

        # Should have 3 participants with distinct personas
        assert len(panel["participants"]) == 3
        personas = [p.get("persona", "") for p in panel["participants"]]
        assert "The Correctness Reviewer" in personas
        assert "The Architecture Reviewer" in personas
        assert "The Risk Reviewer" in personas

        # Each should have a system_prompt with verdict instruction
        for p in panel["participants"]:
            assert "system_prompt" in p
            assert "APPROVE" in p["system_prompt"]

    def test_panels_yaml_has_pre_commit_quick(self):
        """Verify pre-commit-quick panel exists for fast reviews."""
        import yaml
        from pathlib import Path

        panels_path = Path(__file__).parent.parent.parent / "panels.yaml"
        with open(panels_path) as f:
            data = yaml.safe_load(f)

        panels = data["panels"]
        assert "pre-commit-quick" in panels
        panel = panels["pre-commit-quick"]

        assert len(panel["participants"]) == 2
        assert panel["mode"] == "quick"
        assert panel["rounds"] == 1
