# OpenDICOM Sirius RIS Server Operations (via Self-Hosted Runner)

Runner already active in `Madeena-software` under `madeena-devops` group with labels:
`[self-hosted, linux, production]`

No SSH required.

## 1. Secrets Needed in GitHub

Ensure these exist in repo/org secrets:
- `SUDO_PASSWORD`: runner user sudo password (for docker / ufw commands).
- `DOCKER_COMPOSE_ENV`: (optional) contents of `docker-compose.env` if injecting at deploy time.

## 2. Deploying OpenDICOM RIS

1. Go to **Actions** tab -> **Deploy OpenDICOM Sirius RIS (Docker Compose)**.
2. Click **Run workflow**.
3. Options:
   - Action: `up -d --build` (or `up -d`, `restart`, `pull`).
   - Target Service: leave blank for all, or specify `opendicom_sirius_backend`, `opendicom_sirius_frontend`, `opendicom_sirius_database`.

## 3. Server Debugging & Diagnostics

1. Go to **Actions** tab -> **Server Diagnostics & Debug Suite**.
2. Run with targets:
   - `overview`: basic CPU, RAM, disk.
   - `docker`: container stats, exited containers, engine health.
   - `logs`: system and service logs.

## 4. Firewall & Port Rules (UFW)

Use workflow **Server Firewall (UFW) Management** to view rules or open ports safely (includes auto-rollback if lock out).
