---
title: OpenDICOM Sirius RIS Repository Context
document_id: AGENT-CONTEXT-OPENDICOM-SIRIUS-RIS-001
version: 1.0
status: approved-template
language: en-US
scope:
  - repository-level AI orientation
  - opendicom-sirius-ris architecture and operations
authority_note: This context is supporting repository knowledge. Approved repository authority and observed implementation evidence remain controlling.
---

# Repository Context

## Repository identity

**Name:** `opendicom-sirius-ris`
**Repository type:** Radiology Information System (RIS) application and operations
**Primary responsibility:** Radiology information system backend, frontend, database, and operational automation workflows.

## Architecture

- `backend/`: Sirius backend service (Node.js/Express)
- `frontend/`: Sirius frontend UI
- `database/`: Database configuration, dumps, backup cron jobs
- `docker-compose.yml`: Multi-container runtime (database, backend, frontend) on `opendicom_net` network
- `.github/workflows/`: CI/CD and server administration workflows running via self-hosted runner

## Deployment model (No direct SSH)

- Runner already active on production server under `madeena-devops` org runner group.
- Runner labels: `[self-hosted, linux, production]`.
- All deployments, server debugging, and container operations execute locally via GitHub Actions workflows.
- No inbound SSH required.
- Secrets (`SUDO_PASSWORD`, `DOCKER_COMPOSE_ENV`) managed in GitHub Repo / Org secrets.

## Active tasks

- `.agents/tasks/deploy-sirius-ris-via-runner.md` — WP-01: Automate OpenDICOM Sirius RIS Deployment via Self-Hosted Runner.

## Intended authority map

- Repository AI delivery contract: `.agents/AGENTS.md`
- Delivery protocol: `.agents/software-workflow.md`
- Planning and review procedure: `.agents/prompts/plan-create-task.md`
- Validated tasks: `.agents/tasks/`
- Operational workflows: `.github/workflows/`
