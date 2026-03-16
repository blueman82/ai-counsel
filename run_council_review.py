"""Run a council deliberation directly, bypassing MCP layer."""
import asyncio
import json
import sys
import webbrowser
from pathlib import Path

# Add project to path
PROJECT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_DIR))

from adapters import create_adapter
from deliberation.engine import DeliberationEngine
from models.config import load_config
from models.model_registry import ModelRegistry
from models.schema import DeliberateRequest, Participant


async def main():
    # Load config
    config = load_config(str(PROJECT_DIR / "config.yaml"))

    # Create adapters
    adapters = {}
    adapter_sources = []
    if hasattr(config, "adapters") and config.adapters:
        adapter_sources.append(("adapters", config.adapters))
    if hasattr(config, "cli_tools") and config.cli_tools:
        adapter_sources.append(("cli_tools", config.cli_tools))

    for source_name, adapter_configs in adapter_sources.items() if isinstance(adapter_sources, dict) else adapter_sources:
        for cli_name, cli_config in adapter_configs.items():
            if cli_name not in adapters:
                try:
                    adapters[cli_name] = create_adapter(cli_name, cli_config)
                    print(f"Loaded adapter: {cli_name}")
                except Exception as e:
                    print(f"Failed to load adapter {cli_name}: {e}")

    # Create engine
    engine = DeliberationEngine(adapters=adapters, config=config, server_dir=PROJECT_DIR)

    # Read the document
    doc_path = r"c:\Dev\LuxuryApartments\docs\plans\2026-03-16-editorial-review-pipeline-design-v2.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    # Read the v1 transcript for context
    v1_transcript = r"c:\Dev\ai-counsel\transcripts\20260316_085612_council-editorial-pipeline-design-focused.md"
    with open(v1_transcript, "r", encoding="utf-8") as f:
        v1_content = f.read()

    # Extract just the summary and voting sections from v1 (not the full debate)
    # Find the summary section
    summary_start = v1_content.find("# AI Counsel Deliberation Transcript")
    if summary_start == -1:
        summary_start = v1_content.find("## Summary")
    voting_end = v1_content.find("## Full Debate")
    if voting_end == -1:
        v1_summary = v1_content[summary_start:] if summary_start != -1 else ""
    else:
        v1_summary = v1_content[summary_start:voting_end] if summary_start != -1 else ""

    question = f"""Council Review — Editorial Review Pipeline v2

This is a follow-up review of the editorial review pipeline after implementing all changes from your first pipeline-specific review. You unanimously confirmed the P0 was resolved in v1 and provided specific required additions. This v2 implements all of them.

## The Document (v2)

{doc_content}

## Your v1 Review Results (for reference)

{v1_summary}

## What Changed From v1 to v2

Every item from your Final Recommendation has been implemented:

1. **Sampling floor raised from 10% to 20%.** All 4 models required this. Done.
2. **Field notes rendered as styled "Editor's Note" callouts.** Not inline injection. HTML example provided. Immutability rule added — field notes survive Forge regeneration.
3. **CREATE TABLE for la_editorial_content.** Full migration SQL with dependency ordering (20260316000001 before 20260316000002). Includes entity_type, entity_slug, content_version, generated_content jsonb, enrichment_snapshot, status, field_notes with category.
4. **API routes defined.** 6 endpoints: queue list, metrics, detail, claim, approve, reject, request-revision, release. Each with params, guards, and side effects.
5. **State transition table with guards.** 10 explicit transitions. Invariants: only one active queue row per entity, rejected rows immutable, 30-min lock expiry for abandoned reviews.
6. **Minimum 2-minute review duration guard.** fast_review_warning boolean. Reviews under 2 min still go through but are flagged in metrics and Forge data.
7. **Structured rejection_reason_code enum.** 8 codes: weak_verdict, unsupported_claim, thin_comparison, too_promotional, stale_data, poor_local_specificity, formatting_issue, other. Alongside free-text for details.

Additional changes beyond the 7 required:
- B-level upgraded with 3 structured checks (+1 min): verdict defensible? Any claim paused? Would share with friend? Time budget now 6-8 min.
- Circular reference removed. One-directional FK: queue -> content only.
- editorial_review_events append-only audit log.
- Claim-based locking with 30-min expiry.
- Throttle enforcement specified (daily cron job, priority-based FIFO).
- Content preview mechanism (admin page server-renders from editorial table).
- New reviewer roles (content_reviewer, editorial_director).
- Tier transition triggers (5 thresholds).
- Monthly blind audit (20 random skip-tier pages).
- Forge mutation adoption gate (first 3 mutations need human approval).
- High-value entity override (rent >$10K/mo = mandatory review).
- C-level diff_payload for actual text diffs.
- Field notes: 15-char minimum + category + source dropdowns.
- Stale queue handling (7-day warning).

## Your Evaluation Questions (focused — not a full re-review)

1. **Are all required changes correctly implemented?** Check each of the 7 items from your Final Recommendation against the v2 document. Anything missing or misinterpreted?

2. **Does the B-level upgrade (3 structured checks, 6-8 min) strike the right balance?** Opus recommended lightweight binary questions. GPT-5.4 wanted structured claim verification. v2 implements Opus's approach. Is this sufficient, or does GPT-5.4's concern remain valid?

3. **Is the state transition table complete?** 10 transitions with guards. Any missing transitions or edge cases?

4. **Does the throttle cron + claim-based locking adequately handle the operational mechanics?** These were the biggest "hand-wavy" areas in v1.

5. **Updated production readiness score?** v1 scores were 7.8-8.5 (avg 8.2). With all changes implemented, what's the new score?

6. **Is this document now implementation-complete?** Could a developer build this system from v2 without making architectural decisions — only normal clarifying questions?

7. **What, if anything, still prevents shipping?**

Be concise. This is a validation pass, not a deep re-review. If v2 correctly implements your feedback, say so and approve. If something was misinterpreted or a new issue emerged, flag it specifically."""

    request = DeliberateRequest(
        question=question,
        participants=[
            Participant(cli="claude", model="opus", reasoning_effort="high"),
            Participant(cli="openrouter", model="openai/gpt-5.4"),
            Participant(cli="openrouter", model="google/gemini-3.1-pro-preview"),
            Participant(cli="openrouter", model="x-ai/grok-4.20-beta"),
        ],
        rounds=2,
        mode="conference",
        working_directory=r"c:\Dev\LuxuryApartments",
    )

    print(f"\nStarting council deliberation with {len(request.participants)} models, {request.rounds} rounds...")
    print(f"Models: opus@claude, gpt-5.4@openrouter, gemini-3.1-pro@openrouter, grok-4.20@openrouter")
    print(f"Mode: {request.mode}")
    print("This will take several minutes...\n")

    result = await engine.execute(request)

    print(f"\nDeliberation complete!")
    print(f"Rounds: {result.rounds_completed}")
    print(f"Status: {result.status}")

    # Save results
    results_dir = PROJECT_DIR / "results"
    results_dir.mkdir(exist_ok=True)

    from datetime import datetime
    from deliberation.utils import generate_slug

    slug = generate_slug(request.question)
    stem = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slug}"

    result_dict = result.model_dump()

    json_path = results_dir / f"{stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, default=str)

    try:
        from scripts.render_result import render_html
        html_content = render_html(result_dict)
        html_path = results_dir / f"{stem}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML: {html_path}")
        webbrowser.open(str(html_path.resolve()))
    except Exception as e:
        print(f"HTML render failed: {e}")

    print(f"JSON: {json_path}")

    # Print summary
    if result.summary:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(result.summary.consensus)


if __name__ == "__main__":
    asyncio.run(main())
