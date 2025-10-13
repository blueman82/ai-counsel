"""Transcript management for deliberations."""
from datetime import datetime
from pathlib import Path
from typing import Optional
from models.schema import DeliberationResult


class TranscriptManager:
    """
    Manages saving deliberation transcripts.

    Generates markdown files with full debate history and summary.
    """

    def __init__(self, output_dir: str = "transcripts"):
        """
        Initialize transcript manager.

        Args:
            output_dir: Directory to save transcripts (default: transcripts/)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown(self, result: DeliberationResult) -> str:
        """
        Generate markdown transcript from result.

        Args:
            result: Deliberation result

        Returns:
            Markdown formatted transcript
        """
        lines = [
            "# AI Counsel Deliberation Transcript",
            "",
            f"**Status:** {result.status}",
            f"**Mode:** {result.mode}",
            f"**Rounds Completed:** {result.rounds_completed}",
            f"**Participants:** {', '.join(result.participants)}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"**Consensus:** {result.summary.consensus}",
            "",
            "### Key Agreements",
            "",
        ]

        for agreement in result.summary.key_agreements:
            lines.append(f"- {agreement}")

        lines.extend([
            "",
            "### Key Disagreements",
            "",
        ])

        for disagreement in result.summary.key_disagreements:
            lines.append(f"- {disagreement}")

        lines.extend([
            "",
            f"**Final Recommendation:** {result.summary.final_recommendation}",
            "",
            "---",
            "",
            "## Full Debate",
            "",
        ])

        # Group by round
        current_round = None
        for response in result.full_debate:
            if response.round != current_round:
                current_round = response.round
                lines.extend([
                    f"### Round {current_round}",
                    "",
                ])

            lines.extend([
                f"**{response.participant}** ({response.stance})",
                "",
                response.response,
                "",
                f"*{response.timestamp}*",
                "",
                "---",
                "",
            ])

        return "\n".join(lines)

    def save(
        self,
        result: DeliberationResult,
        question: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save deliberation transcript to file.

        Args:
            result: Deliberation result
            question: Original question
            filename: Optional custom filename (default: auto-generated)

        Returns:
            Path to saved file
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create safe filename from question
            safe_question = "".join(c for c in question[:50] if c.isalnum() or c in (' ', '-', '_'))
            safe_question = safe_question.strip().replace(' ', '_')
            filename = f"{timestamp}_{safe_question}.md"

        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'

        filepath = self.output_dir / filename

        # Generate markdown with question at top
        markdown = f"# {question}\n\n" + self.generate_markdown(result)

        # Save
        filepath.write_text(markdown, encoding='utf-8')

        return str(filepath)
