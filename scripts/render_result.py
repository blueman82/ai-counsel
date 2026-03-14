"""Render a deliberation result JSON into a styled HTML report.

Usage:
    python scripts/render-result.py results/20260314_monorepo-review.json
    python scripts/render-result.py c:/tmp/council-review-result.json --output results/

Outputs:
    - {name}.html  (human-readable styled report)
    - {name}.json  (copy of source JSON if --output specified)
"""
import json
import sys
import os
import re
import html
from pathlib import Path
from datetime import datetime


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = text[:max_len].rstrip('-')
    return text


def markdown_to_html(text: str) -> str:
    """Minimal markdown-to-HTML conversion for deliberation responses."""
    lines = text.split('\n')
    result = []
    in_list = False
    in_code = False
    code_lang = ''

    for line in lines:
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                result.append('</code></pre>')
                in_code = False
            else:
                code_lang = line.strip()[3:]
                result.append(f'<pre><code class="language-{html.escape(code_lang)}">')
                in_code = True
            continue

        if in_code:
            result.append(html.escape(line))
            continue

        # Close list if needed
        if in_list and not line.strip().startswith(('- ', '* ', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            result.append('</ul>')
            in_list = False

        # Headers
        if line.startswith('### '):
            result.append(f'<h4>{html.escape(line[4:])}</h4>')
        elif line.startswith('## '):
            result.append(f'<h3>{html.escape(line[3:])}</h3>')
        elif line.startswith('# '):
            result.append(f'<h2>{html.escape(line[2:])}</h2>')
        elif line.startswith('---'):
            result.append('<hr>')
        # List items
        elif line.strip().startswith(('- ', '* ')):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
            result.append(f'<li>{content}</li>')
        # Numbered list
        elif re.match(r'^\d+\.\s', line.strip()):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = re.sub(r'^\d+\.\s*', '', line.strip())
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
            result.append(f'<li>{content}</li>')
        # Paragraphs
        elif line.strip():
            content = html.escape(line)
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
            result.append(f'<p>{content}</p>')

    if in_list:
        result.append('</ul>')
    if in_code:
        result.append('</code></pre>')

    return '\n'.join(result)


def extract_vote(response: str) -> dict | None:
    """Extract VOTE JSON from a response."""
    match = re.search(r'VOTE:\s*(\{[^}]+\})', response)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def vote_color(option: str) -> str:
    """Map vote option to a CSS color."""
    option_lower = option.lower()
    if 'green' in option_lower or 'approve' in option_lower and 'major' not in option_lower:
        return '#22c55e'
    if 'yellow' in option_lower or 'major' in option_lower:
        return '#eab308'
    if 'red' in option_lower or 'reject' in option_lower:
        return '#ef4444'
    return '#6b7280'


def render_html(result: dict) -> str:
    """Render a deliberation result dict into styled HTML."""
    summary = result.get('summary', {})
    convergence = result.get('convergence_info', {})
    debate = result.get('full_debate', [])
    voting = result.get('voting_result', {})

    # Extract question from first round context or use generic
    question_preview = ''
    if debate:
        first = debate[0]
        resp = first.get('response', '')
        # Try to get the question from the prompt (it's not stored directly)
        question_preview = 'Architecture Review'

    # Group by rounds
    rounds = {}
    for entry in debate:
        r = entry.get('round', 1)
        if r not in rounds:
            rounds[r] = []
        rounds[r].append(entry)

    # Collect votes
    votes = []
    for entry in debate:
        vote = extract_vote(entry.get('response', ''))
        if vote:
            votes.append({
                'participant': entry.get('participant', '?'),
                'round': entry.get('round', '?'),
                **vote
            })

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    html_parts = [f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Council Deliberation — {html.escape(question_preview)}</title>
<style>
  :root {{
    --bg: #0f172a;
    --surface: #1e293b;
    --surface-elevated: #334155;
    --border: #475569;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1100px;
    margin: 0 auto;
  }}
  h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
  h2 {{ font-size: 1.35rem; margin: 1.5rem 0 0.75rem; color: var(--accent); }}
  h3 {{ font-size: 1.15rem; margin: 1.25rem 0 0.5rem; }}
  h4 {{ font-size: 1rem; margin: 1rem 0 0.5rem; color: var(--text-muted); }}
  p {{ margin: 0.5rem 0; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }}
  ul {{ margin: 0.5rem 0 0.5rem 1.5rem; }}
  li {{ margin: 0.25rem 0; }}
  code {{
    background: var(--surface-elevated);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.85em;
  }}
  pre {{
    background: var(--surface-elevated);
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin: 0.75rem 0;
  }}
  pre code {{ background: none; padding: 0; }}
  strong {{ color: #f1f5f9; }}

  .meta {{ color: var(--text-muted); font-size: 0.85rem; margin-bottom: 1.5rem; }}
  .summary-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
  }}
  .summary-box h2 {{ margin-top: 0; }}
  .vote-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 0.75rem;
    margin: 1rem 0;
  }}
  .vote-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    border-left: 4px solid var(--accent);
  }}
  .vote-card .participant {{ font-weight: 600; font-size: 0.9rem; }}
  .vote-card .option {{ font-size: 0.85rem; margin-top: 0.25rem; }}
  .vote-card .confidence {{ font-size: 0.8rem; color: var(--text-muted); }}
  .vote-card .rationale {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; font-style: italic; }}

  .round-section {{
    margin: 1.5rem 0;
  }}
  .participant-block {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin: 0.75rem 0;
    overflow: hidden;
  }}
  .participant-header {{
    background: var(--surface-elevated);
    padding: 0.6rem 1rem;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
  }}
  .participant-header:hover {{ background: #3b4f6b; }}
  .participant-header .name {{ font-weight: 600; }}
  .participant-header .chars {{ font-size: 0.8rem; color: var(--text-muted); }}
  .participant-header .toggle {{ font-size: 0.8rem; color: var(--text-muted); }}
  .participant-body {{
    padding: 1rem 1.25rem;
    display: none;
  }}
  .participant-block.open .participant-body {{ display: block; }}
  .participant-block.open .toggle {{ transform: rotate(90deg); }}

  .convergence {{
    display: inline-block;
    background: var(--surface-elevated);
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    font-size: 0.85rem;
    color: var(--text-muted);
  }}
  .tag {{
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
  }}
</style>
</head>
<body>
<h1>AI Council Deliberation</h1>
<div class="meta">
  {html.escape(timestamp)} &middot;
  Mode: {html.escape(result.get('mode', 'unknown'))} &middot;
  Rounds: {result.get('rounds_completed', '?')} &middot;
  <span class="convergence">{html.escape(convergence.get('status', 'unknown'))}</span>
</div>
''']

    # Summary box
    if summary:
        html_parts.append('<div class="summary-box">')
        html_parts.append('<h2>Consensus</h2>')
        consensus_text = summary.get('consensus', '')
        consensus_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(consensus_text))
        html_parts.append(f'<p>{consensus_html}</p>')

        if summary.get('key_agreements'):
            html_parts.append('<h3>Key Agreements</h3><ul>')
            for a in summary['key_agreements']:
                a_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(a))
                html_parts.append(f'<li>{a_html}</li>')
            html_parts.append('</ul>')

        if summary.get('key_disagreements'):
            html_parts.append('<h3>Key Disagreements</h3><ul>')
            for d in summary['key_disagreements']:
                d_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(d))
                html_parts.append(f'<li>{d_html}</li>')
            html_parts.append('</ul>')

        if summary.get('final_recommendation'):
            html_parts.append('<h3>Final Recommendation</h3>')
            rec_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(summary['final_recommendation']))
            html_parts.append(f'<p>{rec_html}</p>')

        html_parts.append('</div>')

    # Votes
    if votes:
        html_parts.append('<h2>Votes</h2>')
        html_parts.append('<div class="vote-grid">')
        # Show latest vote per participant
        latest_votes = {}
        for v in votes:
            latest_votes[v['participant']] = v
        for participant, v in latest_votes.items():
            color = vote_color(v.get('option', ''))
            confidence = v.get('confidence', 0)
            confidence_pct = int(confidence * 100)
            html_parts.append(f'''<div class="vote-card" style="border-left-color: {color}">
  <div class="participant">{html.escape(participant)}</div>
  <div class="option" style="color: {color}">{html.escape(v.get('option', '?'))}</div>
  <div class="confidence">Confidence: {confidence_pct}%</div>
  <div class="rationale">{html.escape(v.get('rationale', '')[:200])}</div>
</div>''')
        html_parts.append('</div>')

    # Rounds
    for round_num in sorted(rounds.keys()):
        entries = rounds[round_num]
        html_parts.append(f'<div class="round-section">')
        html_parts.append(f'<h2>Round {round_num}</h2>')

        for entry in entries:
            participant = entry.get('participant', '?')
            response = entry.get('response', '')
            is_error = response.startswith('[ERROR')
            chars = len(response)

            # Strip VOTE line from display
            display_response = re.sub(r'\nVOTE:.*$', '', response, flags=re.DOTALL).strip()

            open_class = ' open' if round_num == max(rounds.keys()) else ''
            html_parts.append(f'''<div class="participant-block{open_class}">
  <div class="participant-header" onclick="this.parentElement.classList.toggle('open')">
    <span class="name">{html.escape(participant)}</span>
    <span>
      <span class="chars">{chars:,} chars</span>
      <span class="toggle">&#9654;</span>
    </span>
  </div>
  <div class="participant-body">
    {markdown_to_html(display_response) if not is_error else f'<p style="color: var(--red)">{html.escape(response)}</p>'}
  </div>
</div>''')

        html_parts.append('</div>')

    # Footer
    html_parts.append(f'''
<hr>
<div class="meta">
  Generated by <strong>ai-counsel</strong> &middot;
  Participants: {', '.join(p.get('participant', '?') for p in debate[:len(debate)//result.get('rounds_completed', 1)])}
</div>
</body>
</html>''')

    return '\n'.join(html_parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/render-result.py <result.json> [--output <dir>]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    # Parse output directory
    output_dir = input_path.parent
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_dir = Path(sys.argv[idx + 1])
            output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as f:
        result = json.load(f)

    # Generate output filename from timestamp in transcript path or current time
    transcript = result.get('transcript_path', '')
    if transcript:
        # Extract timestamp from transcript filename
        stem = Path(transcript).stem
        name = stem
    else:
        name = datetime.now().strftime('%Y%m%d_%H%M%S_deliberation')

    # Render HTML
    html_content = render_html(result)
    html_path = output_dir / f'{name}.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML: {html_path}")

    # Copy JSON if output dir differs from input dir
    json_path = output_dir / f'{name}.json'
    if json_path.resolve() != input_path.resolve():
        import shutil
        shutil.copy2(input_path, json_path)
        print(f"JSON: {json_path}")
    else:
        print(f"JSON: {input_path} (in place)")


if __name__ == '__main__':
    main()
