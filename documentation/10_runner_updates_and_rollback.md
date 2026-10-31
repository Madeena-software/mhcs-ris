# Production runner updates and rollback

This procedure applies to **Deploy OpenDICOM Sirius RIS (Docker Compose)** on
the other production server, with runner labels `[self-hosted, linux, production]`.
It does not operate the separate Coolify application.

The workflow is manually dispatched. Select the branch containing the updated
workflow and deployment helper. Select `up -d` to update the existing stack;
leave `target_service` empty for all three services, or enter one of:

- `opendicom_sirius_database`
- `opendicom_sirius_backend`
- `opendicom_sirius_frontend`

The server must already have these three Compose containers. Python 3.8+,
Docker Compose v2 with JSON `config` and `up --pull never` support, and Docker
permissions are required. `SUDO_PASSWORD` remains optional for runners that need
sudo. Keep this workflow on the same production host and runner account: recovery
state and retained images are local to that host/account.

## What an update does

1. Checks out deployment tools into `.ris-ci-source` without cleaning the original
   checkout. The original checkout may contain live MongoDB data.
2. Reads the existing containers' Compose labels. Reuses their project name,
   project directory, and absolute storage mount sources. Refuses a missing or
   ambiguous stack instead of creating a separate installation.
3. Checks MongoDB ping and backend/frontend HTTP readiness, plus container health
   checks when configured. Saves the running image IDs under local recovery tags,
   resolved configuration, runtime environment, and environment-file source.
4. Resolves the selected branch's `docker-compose.yml` against the original project
   directory. `DOCKER_COMPOSE_ENV`, when supplied, overrides the existing env-file
   values; without it, the last successful environment source is retained. The
   original `docker-compose.env` remains required for Compose file resolution.
5. Pulls candidate images before changing running services, pins the selected
   image IDs, and reconciles with `up -d --no-build --pull never`. A service-specific
   update uses `--no-deps`; the other services retain their current configuration.
6. Checks readiness for up to 180 seconds. If the update or readiness check fails,
   restores the recorded working stack and checks readiness again. The job stays
   failed even if recovery succeeds, so the failed release remains visible.

The existing Compose file uses published upstream images. `up -d --build` is
retained as a compatibility choice and performs the same image update as `up -d`;
this workflow does not build repository source. Change the image versions in
`docker-compose.yml` when releasing a different published image version. Reusing
an unchanged upstream image will not deploy source-only changes from this repo.

Docker may recreate a changed service container. Project identity and mounted
data remain the same; brief service interruption is possible. New or changed
storage/network layouts are refused. MongoDB's implicit image volumes are also
retained by their existing volume names. If `/app/uploads` contains files without
a covering persistent mount, the update stops: persist those files through a
separately approved migration before recreating the backend.

## Manual rollback and interrupted runs

Dispatch the same workflow with `action: rollback` and an empty `target_service`.
It restores the whole previous working release, including its recorded image
versions and runtime environment. It never guesses a release when no recovery
snapshot exists. A successful first update establishes the manual rollback point.

Before any update mutation, the helper writes a pending recovery record. A runner
crash, job timeout, cancellation, or failed automatic recovery leaves that record
available. Further updates refuse to proceed until `rollback` succeeds. Correct
the underlying host/image/storage problem and retry `rollback` if recovery fails.
Do not delete the recorded state or volumes to retry a deployment.

Recovery files default to `$HOME/.local/state/mhcs-ris-deploy`, owned by the runner
with directory mode `0700` and private files. The optional repository variable
`RIS_DEPLOY_STATE_DIR` can select another private directory outside the checkout.
Keep its value stable. Files contain runtime secrets: do not print them, commit
them, or upload them as workflow artifacts. Recovery tags begin
`mhcs-ris-recovery:`. Avoid pruning these images or deleting the state directory;
they are the local recovery source. Snapshots/tags are retained rather than pruned
automatically. Plan disk housekeeping only after identifying the current,
previous, and pending records that must remain usable.

GitHub concurrency and a nonblocking host file lock prevent overlapping deploy
jobs; newer runs do not cancel an active deployment. Other administration tools
and workflows must also preserve this deployment's data and avoid concurrent
changes. In particular, do not clean the original runner checkout while its
database bind mounts remain there.

## Other operations and limits

- `ps` reports the existing services and their status without pulling images.
- `pull` downloads configured images without changing the running containers.
- `restart` restarts the existing services and checks readiness.
- `down` intentionally **stops** the stack without removing containers, networks,
  or volumes. Leave the service input empty. A later `up -d` first starts that
  recorded release so its data and health can be checked before updating.

Rollback changes application images/configuration; it does not reverse database
writes, schema migrations, or lost files. Take database backups separately and
confirm schema compatibility before changing database/application versions. These
changes have local test evidence; no production dispatch or live recovery drill
has been performed for this workflow update.

Local verification:

```bash
python3 -B -m unittest discover -s tests -p 'test_deploy_compose.py' -v
```

Tests simulate Docker transactions. One test runs real `docker compose config`
against disposable files, without contacting the Docker daemon. It checks that
literal dollars in credentials and absolute mount paths survive recovery-file
serialization. This parsing test is skipped when Docker CLI is unavailable.

References: [Compose configuration rendering](https://docs.docker.com/reference/cli/docker/compose/config/),
[Compose updates and mounted volumes](https://docs.docker.com/reference/cli/docker/compose/up/),
and [GitHub workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
