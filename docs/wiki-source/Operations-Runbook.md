# Operations Runbook

This page is generated from the repository automation configuration.

## Primary health checks

- Application: `/health`
- TTS module: `/tts/health`
- ASR module: `/asr/health`
- Vector module: `/vector/health`

## GitHub automation workflows

- `CI`
- `Infrastructure Checks`
- `CD`
- `AI Triage`
- `Repo Manager`
- `Wiki Sync`
- `PR Curator`
- `Repo Watchdog`
- `Smoke Tests`

## Recovery actions

- Use the `Manual Redeploy` workflow to redeploy an existing image tag.
- Review the latest `[ops]` issues created by automation before manual intervention.
- Re-run `Wiki Sync` after enabling the GitHub Wiki feature.

## Community operations

- `Repo Manager` owns canonical issue/discussion upkeep.
- `AI Triage` owns automated replies and `/ai-reply` drafting.
- `Bootstrap Community` seeds Discussions and setup issues when required.
