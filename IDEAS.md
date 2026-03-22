# Ideas

Future features from the Code Quality Guardian vision (docs/plans/code-quality-guardian-v1.md).
Nothing here blocks launch. These compound over time.

## Tier 2: Learning Flywheel

- **Architecture Debt Tracker** — Persistent ledger of issues with severity, category, resolution status
- **Model Calibration System** — Track per-model accuracy by domain, persist to SQLite
- **Deliberation Chains** — Chain output of one council into the next (quick-check -> code-review -> security-audit)
- **Regression Sentinel** — Auto-detect when past issues recur, escalate severity
- **Confidence-Weighted Recommendations** — Weight opinions by model's historical accuracy

## Tier 3: Growth

- **Live Streaming Web UI** — FastAPI + React, real-time debate visualization, convergence meter
- **CI/CD GitHub Action** — Run reviews on every PR, post findings as comments, block merge on critical
- **Panel Marketplace** — Share/discover community panel presets
- **Zero-Config Quick Start** — Auto-detect adapters, generate config, first deliberation in 60s
- **Before/After Comparison** — Re-run review after fix, show improvement trajectory
- **Risk Dashboard** — Visual summary of active concerns, color-coded, plain-English
- **Codebase Knowledge Graph** — Extend decision graph with architectural knowledge
- **Pattern Library** — Abstract recurring issues into reusable prompt context
- **Cost Tracking** — Token usage and $ per deliberation per model
- **Human-in-the-Loop** — User participates as a council member alongside models

