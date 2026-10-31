#!/usr/bin/env python3
"""Update the existing runner-hosted RIS stack; never provision a second stack."""
import copy
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


SERVICES = tuple("opendicom_sirius_" + name for name in ("database", "backend", "frontend"))
ACTIONS = ("up -d", "up -d --build", "rollback", "restart", "down", "ps", "pull")
UPLOADS_PROBE = """
const fs = require('fs');
function hasUploads(path) {
    return fs.existsSync(path) && fs.readdirSync(path, {withFileTypes: true}).some(entry => {
        const child = path + '/' + entry.name;
        if (entry.isDirectory()) return hasUploads(child);
        // The image includes this empty source-control placeholder.
        return !(entry.name === '.gitkeep' && entry.isFile() && fs.statSync(child).size === 0);
    });
}
process.stdout.write(hasUploads(process.argv[1]) ? 'present' : 'empty');
"""
PROBES = {
    SERVICES[0]: ["mongosh", "--host", SERVICES[0], "--quiet", "--eval", "quit(db.adminCommand('ping').ok ? 0 : 1)"],
    SERVICES[1]: ["node", "-e", "const e=process.env,s=e.SIRIUS_BACKEND_HTTP_ENABLED==='false';require(s?'https':'http').get({hostname:'127.0.0.1',port:s?(e.SIRIUS_BACKEND_HTTPS_PORT||2003):(e.SIRIUS_BACKEND_HTTP_PORT||2000),path:'/',rejectUnauthorized:false},r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"],
    SERVICES[2]: ["wget", "-q", "--spider", "http://127.0.0.1/"],
}


class DeployError(Exception):
    pass


def docker(*args, timeout=600):
    password = os.environ.get("SUDO_PASSWORD", "")
    command = ["sudo", "-S", "-p", "", "docker"] if password else ["docker"]
    # Capture output: rendered Compose/environment and Docker errors may contain secrets.
    try:
        result = subprocess.run(command + list(args), input=password + "\n" if password else None,
                                text=True, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DeployError("Docker command unavailable or timed out") from error
    if result.returncode:
        raise DeployError("Docker command failed: " + " ".join(args[:2]))
    return result.stdout


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def literal(value):
    # Compose interpolates JSON too; runtime passwords containing '$' must stay literal.
    if isinstance(value, str):
        return value.replace("$", "$$")
    if isinstance(value, list):
        return [literal(item) for item in value]
    if isinstance(value, dict):
        return {key: literal(item) for key, item in value.items()}
    return value


def compose(record, *args):
    return docker("compose", "--project-name", record["project"], "--project-directory",
                  record["directory"], "-f", record["file"], *args)


def containers(project=None):
    if project:
        ids = docker("ps", "-aq", "--filter", "label=com.docker.compose.project=" + project).split()
        return json.loads(docker("inspect", *ids)) if ids else []
    return json.loads(docker("inspect", *SERVICES))


def discover(items):
    labels = [item["Config"].get("Labels", {}) for item in items]
    projects = {label.get("com.docker.compose.project") for label in labels}
    directories = {label.get("com.docker.compose.project.working_dir") for label in labels}
    if len(projects) != 1 or None in projects or len(directories) != 1 or None in directories:
        raise DeployError("Existing containers have ambiguous Compose identity")
    if {label.get("com.docker.compose.service") for label in labels} != set(SERVICES):
        raise DeployError("Expected exactly the three existing RIS services")
    files = {label.get("com.docker.compose.project.config_files") for label in labels}
    if len(files) != 1 or None in files:
        raise DeployError("Existing containers have ambiguous Compose config files")
    return {"project": projects.pop(), "directory": directories.pop(), "files": files.pop().split(",")}


def render(meta, files, env_file=None):
    args = ["compose", "--project-name", meta["project"], "--project-directory", meta["directory"]]
    if env_file:
        args += ["--env-file", str(env_file)]
    for file in files:
        args += ["-f", str(file)]
    # `compose config` emits escaped dollars for reuse as a Compose document.
    # Keep the in-memory model literal; store() applies escaping exactly once.
    return json.loads(docker(*args, "config", "--format", "json").replace("$$", "$"))


def mounted_sources(config):
    result = {}
    for service, settings in config["services"].items():
        mounts = {}
        for mount in settings.get("volumes", []):
            source = mount.get("source")
            if mount["type"] == "volume" and source:
                source = config.get("volumes", {}).get(source, {}).get("name", source)
            mounts[mount["target"]] = (mount["type"], source)
        result[service] = mounts
    return result


def verify_mounts(config, items):
    expected = mounted_sources(config)
    for item in items:
        service = item["Config"]["Labels"]["com.docker.compose.service"]
        actual = {mount["Destination"]: (mount["Type"], mount.get("Name") if mount["Type"] == "volume"
                                        else mount["Source"]) for mount in item["Mounts"]}
        if any(actual.get(target) != mount for target, mount in expected[service].items()):
            raise DeployError("Mount configuration differs from running service: " + service)
        for kind, source in actual.values():
            if kind == "bind" and not Path(source).exists():
                raise DeployError("Existing bind source missing; refusing to initialize empty storage")
        for target in actual.keys() - expected[service].keys():
            kind, name = actual[target]
            if kind != "volume" or not name:
                raise DeployError("Unexpected host mount on service: " + service)
            # Preserve implicit image volumes too (e.g. MongoDB /data/configdb).
            key = "retained_" + uuid.uuid4().hex
            config.setdefault("volumes", {})[key] = {"external": True, "name": name}
            config["services"][service].setdefault("volumes", []).append(
                {"type": "volume", "source": key, "target": target})


def ready(project, timeout=180):
    deadline = time.monotonic() + timeout
    while True:
        try:
            items = containers(project)
            by_service = {item["Config"]["Labels"].get("com.docker.compose.service"): item for item in items}
            if set(by_service) != set(SERVICES) or len(items) != len(SERVICES):
                raise DeployError("RIS services missing or duplicated")
            for service in SERVICES:
                item = by_service[service]
                if item["State"]["Status"] != "running":
                    raise DeployError("Service not running: " + service)
                health = item["State"].get("Health", {}).get("Status")
                if health and health != "healthy":
                    raise DeployError("Service not healthy: " + service)
                docker("exec", item["Id"], *PROBES[service], timeout=10)
            print("Readiness passed for database, backend, and frontend.")
            return
        except DeployError:
            if time.monotonic() >= deadline:
                raise DeployError("RIS readiness checks timed out")
            time.sleep(5)


class Deployment:
    def __init__(self, root):
        self.root = root
        self.state_path = root / "state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}

    def save(self, state):
        write_json(self.state_path, state)
        self.state = state

    def record(self, path):
        return json.loads((Path(path) / "record.json").read_text())

    def store(self, meta, config):
        directory = self.root / uuid.uuid4().hex
        directory.mkdir(mode=0o700)
        record = {"project": meta["project"], "directory": meta["directory"],
                  "file": str(directory / "compose.json"), "config": config,
                  "env_text": meta.get("env_text", "")}
        write_json(directory / "compose.json", literal(config))
        write_json(directory / "record.json", record)
        return str(directory), record

    def snapshot(self, meta, config, items):
        config = copy.deepcopy(config)
        verify_mounts(config, items)
        for item in items:
            service = item["Config"]["Labels"]["com.docker.compose.service"]
            # A local tag protects the precise running image even when upstream tags move.
            tag = "mhcs-ris-recovery:" + uuid.uuid4().hex
            docker("image", "tag", item["Image"], tag)
            settings = config["services"][service]
            settings["image"] = tag
            settings.pop("build", None)
            settings.pop("pull_policy", None)
            settings["environment"] = dict(entry.split("=", 1) for entry in item["Config"]["Env"])
        return self.store(meta, config)

    def apply(self, record, target=""):
        for settings in record["config"]["services"].values():
            docker("image", "inspect", settings["image"])
        for mounts in mounted_sources(record["config"]).values():
            for kind, source in mounts.values():
                if kind == "bind" and not Path(source).exists():
                    raise DeployError("Recovery bind source missing; refusing to initialize empty storage")
                if kind == "volume":
                    docker("volume", "inspect", source)
        args = ["up", "-d", "--no-build", "--pull", "never"]
        if target:
            args += ["--no-deps", target]
        compose(record, *args)
        ready(record["project"])

    def rollback(self):
        path = self.state.get("pending") or self.state.get("previous")
        if not path:
            raise DeployError("No previous working release is recorded; rollback refused")
        record = self.record(path)
        # Record recovery intent before mutation; failed/interrupted recovery remains retryable.
        self.save({**self.state, "pending": path})
        self.apply(record)
        self.save({**self.state, "current": path, "pending": None})
        print("Rollback succeeded; existing project and storage retained.")

    def run(self, action, target, source):
        if action not in ACTIONS or (target and target not in SERVICES):
            raise DeployError("Unsupported action or service")
        if action == "rollback":
            if target:
                raise DeployError("Rollback restores the whole stack; leave target_service empty")
            self.rollback()
            return
        if self.state.get("pending"):
            raise DeployError("Interrupted deployment recorded; run rollback before another operation")
        items = containers()
        meta = discover(items)
        if self.state.get("current"):
            current = self.record(self.state["current"])
            if (current["project"], current["directory"]) != (meta["project"], meta["directory"]):
                raise DeployError("Saved deployment identity differs from existing containers")
            config = current["config"]
            meta["env_text"] = current.get("env_text", "")
        else:
            config = render(meta, meta["files"])
            meta["env_text"] = (Path(meta["directory"]) / "docker-compose.env").read_text()
        if set(config["services"]) != set(SERVICES):
            raise DeployError("Only the existing three-service RIS stack is supported")
        verify_mounts(config, items)
        if action == "ps":
            for item in items:
                print(item["Name"].lstrip("/"), item["State"]["Status"],
                      item["State"].get("Health", {}).get("Status", "no healthcheck"))
            return
        if action.startswith("up ") and self.state.get("current") and all(
                item["State"]["Status"] == "exited" for item in items):
            # Resume an intentionally stopped release before checking/snapshotting it.
            # `start` never recreates containers or changes their writable layers.
            compose(current, "start")
            items = containers()
        backend = next(item for item in items if item["Config"]["Labels"]["com.docker.compose.service"] == SERVICES[1])
        if action.startswith("up ") and not any(
                "/app/uploads" == mount["Destination"] or "/app/uploads".startswith(mount["Destination"].rstrip("/") + "/")
                for mount in backend["Mounts"]):
            if backend["State"]["Status"] == "running" and docker(
                    "exec", backend["Id"], "node", "-e", UPLOADS_PROBE, "/app/uploads").strip() == "present":
                raise DeployError("Backend has real unmounted uploads (empty .gitkeep ignored); persist /app/uploads before updating")
        ready(meta["project"])
        previous, record = self.snapshot(meta, config, items)
        if action in ("down", "restart"):
            if action == "down" and target:
                raise DeployError("down does not accept a service; use an empty target")
            # Keep containers/labels discoverable for the next up; never delete storage/networks.
            operation = "stop" if action == "down" else action
            self.save({**self.state, "current": previous})
            compose(record, operation, *([target] if target else []))
            if action == "restart":
                ready(meta["project"])
            return

        # Resolve candidate paths against the existing project, not the new checkout.
        env_file = self.root / "candidate.env"
        secret = os.environ.get("DOCKER_COMPOSE_ENV", "")
        original_env = Path(meta["directory"]) / "docker-compose.env"
        if not original_env.is_file():
            raise DeployError("Existing docker-compose.env missing; refusing to guess configuration")
        env_text = secret or meta.get("env_text") or original_env.read_text()
        env_file.write_text(env_text)
        override = self.root / "candidate-env.json"
        write_json(override, {"services": {name: {"env_file": [str(env_file)]} for name in SERVICES}})
        try:
            candidate = render(meta, [source / "docker-compose.yml", override], env_file)
        finally:
            env_file.unlink(missing_ok=True)
            override.unlink(missing_ok=True)
        if set(candidate["services"]) != set(SERVICES):
            raise DeployError("Candidate changes the service set")
        if any(settings.get("build") for settings in candidate["services"].values()):
            raise DeployError("This workflow updates prebuilt images; source builds require a separate delivery task")
        verify_mounts(candidate, items)
        # The selected operation must not change the other services' configuration.
        if target:
            for service in SERVICES:
                if service != target:
                    candidate["services"][service] = record["config"]["services"][service]
            candidate["volumes"] = {**record["config"].get("volumes", {}), **candidate.get("volumes", {})}
        if candidate.get("networks", {}) != config.get("networks", {}):
            raise DeployError("Candidate changes the existing network configuration")
        meta["env_text"] = env_text
        _, requested = self.store(meta, candidate)
        print("Pulling candidate images; running containers remain untouched.")
        compose(requested, "pull", *([target] if target else []))
        if action == "pull":
            self.save({**self.state, "current": previous})
            print("Images pulled; running deployment unchanged.")
            return
        for service, settings in candidate["services"].items():
            settings["image"] = json.loads(docker("image", "inspect", settings["image"]))[0]["Id"]
        _, requested = self.store(meta, candidate)
        old_state = self.state.copy()
        self.save({**old_state, "current": previous, "pending": previous})
        try:
            self.apply(requested, target)
            current, _ = self.snapshot(meta, candidate, containers(meta["project"]))
            self.save({"current": current, "previous": previous, "pending": None})
        except (DeployError, OSError, ValueError, KeyError) as error:
            print("Update failed; restoring the exact previous images and configuration.")
            try:
                self.apply(record)
                self.save({**old_state, "current": previous, "pending": None})
            except (DeployError, OSError, ValueError, KeyError):
                raise DeployError("Update AND rollback failed; recovery retained. Run rollback after diagnosis.") from error
            raise DeployError("Update failed; rollback succeeded. Requested release was not deployed.") from error
        print("Update succeeded; previous working release is available for rollback.")


def main():
    os.umask(0o077)
    root = Path(os.environ.get("RIS_DEPLOY_STATE_DIR") or Path.home() / ".local/state/mhcs-ris-deploy").resolve()
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd())).resolve()
    if root == workspace or workspace in root.parents:
        raise DeployError("Recovery directory must be outside the Actions checkout")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise DeployError("Recovery directory must be owned by the runner and mode 0700")
    with (root / "deploy.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise DeployError("Another deployment holds the host lock") from error
        Deployment(root).run(os.environ.get("DEPLOY_ACTION", "up -d"),
                             os.environ.get("TARGET_SERVICE", ""), Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    try:
        main()
    except (DeployError, OSError, ValueError, KeyError) as error:
        # Never echo exception content from JSON or environment parsing.
        print(str(error) if isinstance(error, DeployError) else "Deployment state/configuration is invalid", file=sys.stderr)
        sys.exit(1)
