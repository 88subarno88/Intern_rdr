# Internship Radar (n8n + Claude Pro)

A personal robot that checks your Gmail and a few RSS feeds every 3 hours, asks Claude
which messages are real internships or cool projects, and mails you a short digest.
At 10 pm it mails one end-of-day wrap.

**Running cost: ₹0/month.** n8n runs on your laptop, Claude runs through the Claude Code
login you already pay for with Pro. No API keys are bought anywhere.

## Status (2026-10-08)

| Part | State |
|---|---|
| n8n 2.42.4 installed, running as a background service on <http://localhost:5678> | Done |
| Claude scoring step inside n8n | Done, tested |
| RSS → filter → dedupe → Claude → digest mail body | Done, tested with live feeds |
| Daily wrap mail body | Done, tested |
| Workflows `Radar - 3 hourly` and `Radar - daily wrap` imported into n8n | Done, switched off |
| Gmail connection (reading mail and sending the digest) | Done, first real run mailed a digest |
| Both workflows published (timers on) | Done |
| Resume-based rating, two-section mail | Done, see `03_workflow_3hourly.md` |
| Discord branch in the workflow | Added, switched off until you connect a bot (`02_setup.md`, section E) |
| Twitter/X | Left out on purpose, see `05_sources.md` |

## Upkeep

- Gmail is reached with an app password, which does not expire. See
  `07_gmail_login_fix.md` if it ever needs replacing.
- When your resume changes, update the resume section in `prompts/score_prompt.md`.

## Files

| File | What it explains |
|---|---|
| `PROGRESS.md` | What has been done so far, what is pending, and notes for resuming |
| `01_how_it_works.md` | The whole model in plain words, with a diagram |
| `02_setup.md` | What is installed, and the Gmail steps left for you |
| `03_workflow_3hourly.md` | The main workflow, node by node |
| `04_workflow_daily.md` | The end-of-day wrap workflow |
| `05_sources.md` | Where opportunities come from and how to add more |
| `07_gmail_login_fix.md` | How the Gmail login works (app password) and how to replace it |
| `06_limits_and_fixes.md` | Limits, costs, service commands, troubleshooting |
| `prompts/` | Claude's instructions (edit your profile here), plus a test script |
| `workflows/` | Copies of the workflows, in case you ever need to re-import them |
| `tools/` | Scripts that build and test the workflows, and `mail_template.js`, the mail design |
| `previews/` | Pictures of what the two mails look like |
