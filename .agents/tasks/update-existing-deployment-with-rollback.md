---
title: Update the existing RIS deployment with rollback
document_id: AGENT-TASK-RIS-002
version: 1.0
status: validated-published
language: en-US
last_updated: 2026-10-31
---

# Executable Task

## Task identity and delivery context

Task path: `.agents/tasks/update-existing-deployment-with-rollback.md`.
Contract state: **Validated/Published**, effective at the immutable local
publication commit containing this revision.
Owner/designated authority: requesting repository owner.
Objective: update GitHub Actions so subsequent releases update the existing RIS
deployment, preserve persistent data, and support recovery to a working release.
The user confirmed the target is the other server operated by the existing
`.github/workflows/deploy-docker-compose.yml`, not Coolify.

## Baseline and task revision

Implementation baseline: `24ff711b145228492bffddaab37ca1081640978b`.
Task revision: resolve from the local publication commit containing this content
before starting execution; supplied explicitly in the execution handoff.
No accepted baseline for this new objective has been established by this planning
pass. The implementation baseline is the observed clean repository HEAD.

## Authoritative inputs and requirement traceability

- Human request, 2026-10-31: update GitHub CI/CD to update the previous deployment
  rather than create a replacement deployment, with rollback on failure.
- `.agents/AGENTS.md` and `.agents/software-workflow.md` govern execution,
  publication, evidence, and release boundaries.
- RIS-CD-01: reuse the existing deployment identity and persistent storage.
- RIS-CD-02: retain an identifiable working release and offer manual rollback.
- RIS-CD-03: detect an unsuccessful rollout and attempt recovery automatically;
  report rollout and recovery outcomes separately, retaining a failed job status
  for an unsuccessful requested rollout.
- RIS-CD-04: serialize operations for the same deployment and avoid interrupting
  a rollout with a newer run.

The human's subsequent instruction, “Implement it”, approves the presented
contract, automatic/manual recovery, and local task/implementation commits.

## Observed evidence and pending delivery state

The existing workflow `.github/workflows/deploy-docker-compose.yml` executes
Compose in the Actions checkout and pulls fixed upstream image versions. It has
no rollback action or health-based recovery. The historical runner task is
`.agents/tasks/deploy-sirius-ris-via-runner.md` at
`d340d5149d09f596fd943f1b44392244690ba112`; operational acceptance evidence for
that task has not been established here. This draft does not declare it accepted.

The workflow runs on `[self-hosted, linux, production]`. `docker-compose.yml`
uses fixed container names and relative host mounts for MongoDB data, dumps,
cron configuration, and backups. The application images come from upstream,
so `up -d --build` currently has no source build definitions to build. Changing
the checkout/project directory could select different data paths. Checkout
cleanup is another risk for data held under the runner workspace. These are
configuration observations; this pass has not inspected live deployment state.

Planning state: **READY FOR PUBLICATION**. Target and approval decisions are
resolved. T5 passes when the local immutable publication commit is observed.
Do not expand the historical task
or start implementation under its older contract.

## Dependencies and decisions required before publication

1. Target resolved by the human: existing Docker Compose stack on the production
   self-hosted runner. No Coolify changes.
2. Historical task's live acceptance remains unverified; no new production
   acceptance is claimed or required to author this local workflow correction.
3. Resolved: “Implement it” authorizes this bounded contract and local
   task-publication and verified implementation commits. No push or deployment.
4. The workflow must establish the existing Compose project identity and absolute
   persistent mount paths from Docker metadata before an update; refuse ambiguous
   or missing existing-deployment state instead of provisioning a new stack.

## Scope and constraints

In scope: the selected GitHub deployment workflow, a small deployment helper and
focused tests if necessary, deployment instructions, and existing STATE/WORKLOG
records. Reuse Docker Compose and preserve the existing dispatch operations
where compatible with safe updates. Add a whole-stack rollback dispatch action.

Preserve: deployment identity, persistent database/backups/uploads storage,
runtime secrets, existing language settings, existing service dependencies,
and unrelated applications. Replacing application containers during an update
is permitted; creating a second application/project or deleting storage is not.

Out of scope: application features, schema changes, database restoration,
infrastructure provisioning, unrelated workflow changes, dependency additions,
host Docker daemon reconfiguration, pushing, or triggering a live deployment.

No inbound SSH. Do not log secrets or interpolate untrusted workflow inputs into
shell program text. Keep production secrets outside runner checkout cleanup.
Preserve project identity from the existing containers' Compose labels; preserve
absolute host mount sources. Store recovery manifests/configuration with private
permissions outside checkout cleanup. Retain the running image IDs locally under
immutable recovery references before pulling updated images. Updates must use
Compose reconciliation without tearing down the stack first. Do not modify the
Docker daemon configuration as a deployment step. Acquire a deployment lock and
avoid unsafe checkout cleanup before inspecting an existing deployment.
Do not claim application rollback restores database contents. Stop for authority
if a release introduces a database compatibility or migration decision.

## Acceptance criteria

- Repeated successful updates retain the selected application's/project's
  identity, service configuration, persistent mounts, and existing data.
- The previous working release is recorded before mutation and remains usable
  if the new release fails. Recovery uses that exact release, not a mutable tag
  or a moving branch tip.
- Readiness is checked with a bounded timeout. Failed builds/pulls/readiness
  checks do not silently mark a release successful.
- A failed rollout automatically attempts recovery when a working release exists;
  recovery failure is reported clearly. Missing recovery information causes a
  safe explicit refusal before mutation, rather than guessing a release.
- Manual rollback is available through workflow dispatch and checks readiness.
- Concurrent runs cannot mutate the same deployment simultaneously or cancel an
  in-progress recovery. Inputs are validated, and credentials remain masked.

## Verification requirements and evidence

Validate GitHub Actions syntax and helper shell/program syntax. Add focused,
isolated tests for successful update, failed rollout with successful recovery,
failed recovery, absent previous-release state, and manual rollback. Verify
that update/recovery commands address the same deployment and preserve storage.
Use mocks or disposable fixtures; do not operate production containers in tests.

Report actual commands, outcomes, changed paths, exact implementation revision or
working-tree state, deviations, and unavailable checks. Live production rollout
and data preservation remain unverified until separately authorized and observed.

## Capabilities, side effects, and stop conditions

Required capabilities: repository reads/writes, local shell, isolated tests, and
read-only platform documentation when needed. Publication requires a local Git
commit, authorized by the human's “Implement it” response. Local implementation
and verification commits are also authorized. No push, release, secret access,
external mutation, or production operation is authorized by this task.

Stop for unresolved target, unavailable immutable governing task revision,
unresolved relevant prior review, incompatible persistent-storage identity,
unsupported rollback mechanism, missing authority, materially expanded scope,
or a verification requirement that cannot be satisfied safely.

## Expected terminal outcome and review

Current outcome: **Execution Required** after immutable publication.
After publication, the Executor returns **Review Required** with observed local
evidence, or **Planning Required** with the exact blocking condition. Reviewer
evaluates the immutable governing task and implementation independently of release
authorization. Implementation acceptance does not authorize a live rollout.
