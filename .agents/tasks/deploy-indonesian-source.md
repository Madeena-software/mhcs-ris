---
title: Deploy Indonesian source through the production runner
document_id: AGENT-TASK-RIS-003
version: 1.0
status: validated-published
language: en-US
last_updated: 2026-10-31
---

# Executable Task

Owner/designated authority: requesting repository owner.
Task path: `.agents/tasks/deploy-indonesian-source.md`.
Implementation baseline: `44dfaf2b1c99a5c793df8ee1628fe93f4678d7b7`.
Governing revision: the immutable publication commit containing this content,
resolved by Git before implementation and recorded in the execution handoff.

## Delivery state and authority

The user's instruction, “Okay, set that in workflow then trigger it again”,
following the explanation that Indonesian requires repository-built images and
`SIRIUS_LANGUAJE=id` on frontend/backend, authorizes this bounded change, its
necessary task/implementation commits, push to main, and production dispatch.
The existing task explicitly excludes source builds; this is its successor.
The prior remediation at the baseline is accepted for its bounded upload guard:
source review preserves real-file/symlink detection, all 25 local tests pass,
and production run `41205935652` succeeded at that exact revision. Live rollback
drills remain unverified. No conflicting pending implementation was observed.

B0/P1: enable Indonesian on the existing runner-hosted deployment.
R2: RIS-ID-CD-01 builds this repository's frontend/backend; RIS-ID-CD-02 sets
Indonesian on both; RIS-ID-CD-03 preserves project, data and exact recovery;
RIS-ID-CD-04 dispatches the changed main workflow and reports observed results.
A3/D4: reuse existing Dockerfiles, Compose transaction helper, runner labels,
private recovery snapshots, concurrency and host lock. No schema changes.
T5: ready when this contract has an immutable publication revision.
Repository contracts `.agents/AGENTS.md` and `.agents/software-workflow.md`
remain controlling; setup evidence is `documentation/08_indonesian_language.md`.

## Scope and constraints

Update the deployment workflow/helper, focused tests and existing operations,
STATE/WORKLOG/context records. Build selected frontend/backend images from the
checked-out revision for updates, before running-container mutation, under the
existing lock. Use distinct local image tags and pin the resulting IDs. Keep
the database image and storage unchanged. Set `SIRIUS_LANGUAJE=id` on selected
app services explicitly, taking precedence over any retained environment file.
Keep other dispatch operations and service-specific scope working. Existing
mount/network/upload safety, readiness, automatic/manual rollback and private
secret handling remain mandatory. Reuse existing Dockerfiles without new build
dependencies or frameworks. Do not modify Coolify, provision another stack,
expose secrets, migrate/delete data, or alter unrelated services.

## Acceptance and verification

- Workflow updates build repository app images and apply Indonesian settings.
- Build failures leave running containers unchanged; rollout/readiness failure
  restores the exact previous images and environment and fails the run.
- Existing data/mount, network, locking and upload guards remain effective.
- Partial updates build/change only selected application services; rollback
  retains all prior language settings. Pull remains a prebuilt-image operation.
- Run the existing suite plus tests for source builds, language precedence,
  build failure, partial updates, safety refusal and rollback with source mode.
  Validate Python syntax, Actions syntax and diff formatting. Check both existing
  Indonesian dictionary validators. Observe the dispatched workflow's tests,
  builds, readiness and terminal result; report any blocked/live gaps honestly.

## Side effects, stop conditions and handoff

Authorized: bounded repository edits, local publication/implementation commits,
push to `origin/main`, and dispatch/monitor the production workflow with a whole
stack update. Dependencies installed inside the existing image build are part
of this authorization. No local production-container operation is required.
Stop for missing immutable identity, ambiguous live project/storage, real
unmounted uploads, schema compatibility decisions, unavailable required checks,
or material scope expansion. Never bypass guards to make a run pass.
Executor returns Review Required with exact revisions and observed checks;
Reviewer accepts the immutable implementation before the authorized dispatch.
Production failure requires bounded diagnosis/remediation or an explicit blocker.
