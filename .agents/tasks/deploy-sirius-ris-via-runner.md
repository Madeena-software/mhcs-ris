---
title: Automate OpenDICOM Sirius RIS Deployment via Self-Hosted Runner
document_id: AGENT-TASK-RIS-001
version: 1.0
status: validated-published
language: en-US
last_updated: 2026-10-22
scope:
  - opendicom-sirius-ris docker-compose deployment automation
  - self-hosted runner integration via madeena-devops runner pool
  - deployment verification without inbound SSH
authority_note: A published validated task authorizes only the bounded implementation scope explicitly defined by the task and applicable approved repository authority. Observed repository evidence governs claims about current implementation reality but does not silently redefine the task or its intended authority.
---

# Executable Task

## Task identity

**Task title:**  
Automate OpenDICOM Sirius RIS Deployment via Self-Hosted Runner

**Task path:**  
`.agents/tasks/deploy-sirius-ris-via-runner.md`

**Task contract state:**  
`Validated/Published`

**Delivery objective / Work Package / MVP:**  
WP-01 — Sirius RIS Docker Compose Deployment via GitHub Actions Self-Hosted Runner

**Owner / designated planning authority:**  
Designated Human Authority / Repository Planner

## Delivery context

The `opendicom-sirius-ris` repository contains the RIS backend, frontend, database, and docker-compose configurations.
Direct inbound SSH to the deployment host is unavailable.
An organization-level runner pool (`madeena-devops`) is already active on the target Linux production host (`[self-hosted, linux, production]`).
Deployment, diagnostics, and container operations must be executed directly through GitHub Actions workflows running locally on the self-hosted runner without SSH.

## Baseline and task revision

**Implementation baseline:**  
`60016dd0f92cf602d6fd262574e35ecc0cf29989`

**Task revision:**  
Resolved upon publication commit to `main` (`.agents/tasks/deploy-sirius-ris-via-runner.md` @ published Git commit SHA).

## Objective

1. Maintain `.github/workflows/deploy-docker-compose.yml` configured with `runs-on: [self-hosted, linux, production]`.
2. Support `workflow_dispatch` actions (`up -d --build`, `up -d`, `down`, `restart`, `pull`, `ps`).
3. Inject environment configuration safely via secret `DOCKER_COMPOSE_ENV` if defined.
4. Execute deployment commands locally via `SUDO_PASSWORD` (or direct docker permissions if in docker group).
5. Verify container health status post-deployment via `docker compose ps`.

## Acceptance criteria

1. Workflow dispatch can target all services or an individual service (`opendicom_sirius_backend`, `opendicom_sirius_frontend`, `opendicom_sirius_database`).
2. No inbound SSH is used or required.
3. Operational secrets are never logged or persisted insecurely.
4. Deployment status and running containers are visibly output in GitHub Actions job logs.

## Verification requirements

- Stage A (Static verification):
  - Workflow syntax valid under GitHub Actions schema.
  - Runner labels match active runner pool (`[self-hosted, linux, production]`).
- Stage B (Operational verification):
  - Manual dispatch on production runner succeeds with exit code 0.
  - `docker compose ps` shows database, backend, and frontend containers in healthy/running state.

## Stop conditions

- Inbound SSH connection requested or required.
- Hardcoded secrets or private keys placed in version control.
- Runner labels misconfigured causing jobs to hang waiting for nonexistent runners.
