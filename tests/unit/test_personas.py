"""Unit tests for persona and system_prompt support."""
import pytest
from models.schema import Participant


class TestParticipantPersona:
    """Tests for persona fields on Participant model."""

    def test_persona_is_optional(self):
        p = Participant(cli="claude", model="sonnet")
        assert p.persona is None
        assert p.system_prompt is None

    def test_persona_set(self):
        p = Participant(
            cli="claude",
            model="opus",
            persona="The Strategist",
        )
        assert p.persona == "The Strategist"

    def test_system_prompt_set(self):
        p = Participant(
            cli="openrouter",
            model="x-ai/grok-4",
            persona="The Attacker",
            system_prompt="You are a penetration tester. Find all vulnerabilities.",
        )
        assert p.persona == "The Attacker"
        assert "penetration tester" in p.system_prompt

    def test_backward_compatibility(self):
        """Existing participant dicts without persona/system_prompt still work."""
        p = Participant(
            cli="claude",
            model="sonnet",
            reasoning_effort="high",
        )
        assert p.persona is None
        assert p.system_prompt is None
        assert p.reasoning_effort == "high"

    def test_from_panel_dict(self):
        """Simulate loading from panels.yaml dict."""
        panel_data = {
            "cli": "claude",
            "model": "opus",
            "persona": "The Creative Director",
            "system_prompt": "You evaluate design through a luxury brand lens.",
        }
        p = Participant(**panel_data)
        assert p.persona == "The Creative Director"
        assert "luxury brand" in p.system_prompt

    def test_participant_id_with_persona(self):
        """Test the participant ID format used in transcripts."""
        p = Participant(
            cli="claude",
            model="opus",
            persona="The Strategist",
        )
        # Engine builds ID like: "The Strategist (opus@claude)"
        participant_id = (
            f"{p.persona} ({p.model}@{p.cli})"
            if p.persona
            else f"{p.model}@{p.cli}"
        )
        assert participant_id == "The Strategist (opus@claude)"

    def test_participant_id_without_persona(self):
        """Without persona, falls back to model@cli format."""
        p = Participant(cli="claude", model="sonnet")
        participant_id = (
            f"{p.persona} ({p.model}@{p.cli})"
            if p.persona
            else f"{p.model}@{p.cli}"
        )
        assert participant_id == "sonnet@claude"
