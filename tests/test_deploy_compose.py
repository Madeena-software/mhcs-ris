"""Deployment transaction tests use a fake Docker engine; no live Docker access."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("deploy", Path(__file__).resolve().parents[1] / "scripts/deploy_compose.py")
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


class DockerDiagnosticsTests(unittest.TestCase):
    def test_build_failure_shows_diagnostics_but_other_commands_stay_private(self):
        for command, visible in [("build", True), ("compose", False), ("inspect", False)]:
            with self.subTest(command=command), patch.object(deploy.subprocess, "run", return_value=
                    subprocess.CompletedProcess([], 1, stdout="", stderr="diagnostic detail")), \
                    patch("sys.stderr", new=io.StringIO()) as output:
                with self.assertRaises(deploy.DeployError):
                    deploy.docker(command, "test")
                self.assertEqual("diagnostic detail" in output.getvalue(), visible)


class FakeDocker:
    def __init__(self, directory):
        self.directory = directory
        self.config = {"name": "original-project", "services": {
            service: {"image": "upstream/" + service + ":old", "environment": {"PASSWORD": "old$literal"},
                      "volumes": [{"type": "bind", "source": str(directory), "target": "/data"}]}
            for service in deploy.SERVICES}}
        self.candidate = copy.deepcopy(self.config)
        for service in deploy.SERVICES:
            self.candidate["services"][service]["image"] = "upstream/" + service + ":new"
            self.candidate["services"][service]["environment"]["PASSWORD"] = "new$literal"
        self.images = {settings["image"]: "sha256:old" + str(index)
                       for index, settings in enumerate(self.config["services"].values())}
        self.images.update({settings["image"]: "sha256:new" + str(index)
                            for index, settings in enumerate(self.candidate["services"].values())})
        self.calls = []
        self.up_failures = []
        self.pull_failure = False
        self.build_failure = False
        self.language_mismatch = False
        self.status = "running"

    def items(self):
        return [{"Id": service, "Name": "/" + service, "Image": self.images.get(settings["image"], settings["image"]),
                 "Config": {"Labels": {"com.docker.compose.project": "original-project",
                                       "com.docker.compose.project.working_dir": str(self.directory),
                                       "com.docker.compose.project.config_files": str(self.directory / "old.yml"),
                                       "com.docker.compose.service": service},
                            "Env": [key + "=" + value for key, value in settings["environment"].items()]},
                 "State": {"Status": self.status},
                 "Mounts": [{"Type": "bind", "Source": str(self.directory), "Destination": "/data"}]}
                for service, settings in self.config["services"].items()]

    def __call__(self, *args, **kwargs):
        self.calls.append(args)
        if args[0] == "inspect":
            return json.dumps(self.items())
        if args[0] == "ps":
            return " ".join(deploy.SERVICES)
        if args[0] == "exec":
            if args[-1] == "http://127.0.0.1/assets/main-settings.json":
                language = "en" if self.language_mismatch else self.config["services"][deploy.SERVICES[2]]["environment"]["SIRIUS_LANGUAJE"]
                return json.dumps({"appSettings": {"language": language}, "FullCalendarOptions": {"locale": language},
                                   "CKEditorConfig": {"language": {"ui": language, "content": language}}})
            if args[-1] == "http://127.0.0.1/assets/i18n/id.json":
                return '{"label":"Indonesian fixture"}'
            return ""
        if args[0] == "build":
            if self.build_failure:
                raise deploy.DeployError("Build failed")
            image = args[args.index("--tag") + 1]
            self.images[image] = "sha256:source-" + Path(args[-1]).name
            return ""
        if args[:2] == ("image", "tag"):
            self.images[args[3]] = args[2]
            return ""
        if args[:2] == ("image", "inspect"):
            return json.dumps([{"Id": self.images.get(args[2], args[2])}])
        if args[0] == "compose":
            assert args[1:3] == ("--project-name", "original-project")
            assert args[3:5] == ("--project-directory", str(self.directory))
            if "config" in args:
                value = self.candidate if str(self.directory / "docker-compose.yml") in args else self.config
                return json.dumps(deploy.literal(value))
            if "pull" in args:
                if self.pull_failure:
                    raise deploy.DeployError("Pull failed")
                return ""
            if "up" in args:
                raw = json.loads(Path(args[args.index("-f") + 1]).read_text())
                config = json.loads(json.dumps(raw).replace("$$", "$"))
                if args[-1] in deploy.SERVICES:
                    service = args[-1]
                    self.config["services"][service] = config["services"][service]
                else:
                    self.config = config
                self.status = "running"
                # Simulate a partially applied update that then fails.
                if self.up_failures and self.up_failures.pop(0):
                    raise deploy.DeployError("Up failed")
                return ""
            if "stop" in args:
                self.status = "exited"
                return ""
            if "restart" in args or "start" in args:
                self.status = "running"
                return ""
        raise AssertionError("Unexpected Docker call: " + repr(args))


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        # Fake deployment successes must not look like live deployment evidence in CI logs.
        output = patch("sys.stdout", new=io.StringIO())
        output.start()
        self.addCleanup(output.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.state_root = self.directory / "state"
        self.state_root.mkdir()
        (self.directory / "docker-compose.env").write_text("PASSWORD=old$literal\n")
        self.engine = FakeDocker(self.directory)
        self.patcher = patch.object(deploy, "docker", side_effect=self.engine)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.environment = patch.dict(os.environ, {"DOCKER_COMPOSE_ENV": "", "RIS_BUILD_SOURCE": "", "SIRIUS_LANGUAJE": ""})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.deployment = deploy.Deployment(self.state_root)

    def run_action(self, action="up -d", target=""):
        self.deployment.run(action, target, self.directory)

    def images(self):
        return [item["Image"] for item in self.engine.items()]

    def test_success_records_original_images_environment_and_project(self):
        self.run_action()
        self.assertTrue(all(image.startswith("sha256:new") for image in self.images()))
        previous = self.deployment.record(self.deployment.state["previous"])
        self.assertEqual(previous["project"], "original-project")
        self.assertEqual(previous["directory"], str(self.directory))
        for settings in previous["config"]["services"].values():
            self.assertEqual(settings["environment"]["PASSWORD"], "old$literal")
            self.assertTrue(settings["image"].startswith("mhcs-ris-recovery:"))
        self.assertIn("old$$literal", Path(previous["file"]).read_text())
        self.assertFalse(self.deployment.state["pending"])

    def test_source_update_builds_apps_and_overrides_language_then_rollback_restores_it(self):
        for settings in self.engine.config["services"].values():
            settings["environment"]["SIRIUS_LANGUAJE"] = "es"
        for settings in self.engine.candidate["services"].values():
            settings["environment"]["SIRIUS_LANGUAJE"] = "en"
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            self.run_action()
            self.assertEqual(self.images(), ["sha256:new0", "sha256:source-backend", "sha256:source-frontend"])
            for service in deploy.SERVICES[1:]:
                self.assertEqual(self.engine.config["services"][service]["environment"]["SIRIUS_LANGUAJE"], "id")
            pulls = [call for call in self.engine.calls if "pull" in call and "up" not in call]
            self.assertEqual(len(pulls), 1)
            self.assertEqual(pulls[0][-1], deploy.SERVICES[0])
            self.run_action("rollback")
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])
        for settings in self.engine.config["services"].values():
            self.assertEqual(settings["environment"]["SIRIUS_LANGUAJE"], "es")

    def test_source_build_failure_leaves_containers_unchanged(self):
        self.engine.build_failure = True
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            with self.assertRaisesRegex(deploy.DeployError, "Build failed"):
                self.run_action()
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])
        self.assertFalse(any("up" in call for call in self.engine.calls))

    def test_source_partial_update_builds_only_selected_app(self):
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            self.run_action(target=deploy.SERVICES[2])
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:source-frontend"])
        self.assertEqual(sum(call[0] == "build" for call in self.engine.calls), 1)
        self.assertFalse(any("pull" in call and "up" not in call for call in self.engine.calls))

    def test_source_apply_failure_restores_old_images(self):
        self.engine.up_failures = [True, False]
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            with self.assertRaisesRegex(deploy.DeployError, "rollback succeeded"):
                self.run_action()
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])

    def test_source_mount_guard_runs_before_build(self):
        self.engine.candidate["services"][deploy.SERVICES[0]]["volumes"][0]["source"] = "/wrong"
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true"}):
            with self.assertRaisesRegex(deploy.DeployError, "Mount configuration differs"):
                self.run_action()
        self.assertFalse(any(call[0] == "build" for call in self.engine.calls))

    def test_source_language_mismatch_rolls_back(self):
        self.engine.language_mismatch = True
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            with self.assertRaisesRegex(deploy.DeployError, "rollback succeeded"):
                self.run_action()
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])

    def test_pull_does_not_build_even_with_source_mode(self):
        with patch.dict(os.environ, {"RIS_BUILD_SOURCE": "true", "SIRIUS_LANGUAJE": "id"}):
            self.run_action("pull")
        self.assertFalse(any(call[0] == "build" for call in self.engine.calls))
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])

    def test_manual_rollback_restores_exact_old_images_and_environment(self):
        self.run_action()
        self.run_action("rollback")
        self.assertTrue(all(image.startswith("sha256:old") for image in self.images()))
        for settings in self.engine.config["services"].values():
            self.assertEqual(settings["environment"]["PASSWORD"], "old$literal")

    def test_failed_apply_recovers_but_still_fails_job(self):
        self.engine.up_failures = [True, False]
        with self.assertRaisesRegex(deploy.DeployError, "rollback succeeded"):
            self.run_action()
        self.assertTrue(all(image.startswith("sha256:old") for image in self.images()))
        self.assertFalse(self.deployment.state["pending"])

    def test_failed_readiness_recovers(self):
        with patch.object(deploy, "ready", side_effect=[None, deploy.DeployError("unhealthy"), None]):
            with self.assertRaisesRegex(deploy.DeployError, "rollback succeeded"):
                self.run_action()
        self.assertTrue(all(image.startswith("sha256:old") for image in self.images()))

    def test_failed_recovery_retains_pending_state_for_manual_retry(self):
        self.engine.up_failures = [True, True]
        with self.assertRaisesRegex(deploy.DeployError, "AND rollback failed"):
            self.run_action()
        self.assertTrue(self.deployment.state["pending"])
        with self.assertRaisesRegex(deploy.DeployError, "Interrupted"):
            self.run_action()
        deploy.Deployment(self.state_root).run("rollback", "", self.directory)
        self.assertTrue(all(image.startswith("sha256:old") for image in self.images()))

    def test_missing_previous_refuses_before_mutation(self):
        with self.assertRaisesRegex(deploy.DeployError, "No previous"):
            self.run_action("rollback")
        self.assertEqual(self.engine.calls, [])

    def test_pull_failure_does_not_touch_running_stack(self):
        self.engine.pull_failure = True
        with self.assertRaisesRegex(deploy.DeployError, "Pull failed"):
            self.run_action()
        self.assertFalse(any("up" in call for call in self.engine.calls))
        self.assertTrue(all(image.startswith("sha256:old") for image in self.images()))

    def test_changed_mount_refused_before_pull_or_update(self):
        self.engine.candidate["services"][deploy.SERVICES[0]]["volumes"][0]["source"] = "/wrong"
        with self.assertRaisesRegex(deploy.DeployError, "Mount configuration differs"):
            self.run_action()
        self.assertFalse(any("up" in call or "pull" in call for call in self.engine.calls))

    def test_partial_update_changes_only_requested_service(self):
        self.run_action(target=deploy.SERVICES[2])
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:new2"])
        self.run_action("rollback")
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])

    def test_repeat_update_uses_upstream_refs_and_keeps_previous_release(self):
        self.run_action()
        self.run_action()
        self.run_action("rollback")
        self.assertTrue(all(image.startswith("sha256:new") for image in self.images()))

    def test_down_stops_without_removing_and_up_reuses_identity(self):
        self.run_action("down")
        self.assertEqual(self.engine.status, "exited")
        self.run_action()
        self.assertEqual(self.engine.status, "running")
        self.assertFalse(any("down" in call for call in self.engine.calls))

    def test_invalid_input_and_partial_rollback_rejected(self):
        for action, target in [("up -d; bad", ""), ("up -d", "$(bad)"), ("rollback", deploy.SERVICES[0])]:
            with self.assertRaises(deploy.DeployError):
                self.run_action(action, target)
        self.assertEqual(self.engine.calls, [])

    def test_ambiguous_existing_identity_refused(self):
        items = self.engine.items()
        items[0]["Config"]["Labels"]["com.docker.compose.project"] = "other"
        with self.assertRaisesRegex(deploy.DeployError, "ambiguous"):
            deploy.discover(items)

    def test_image_anonymous_volumes_are_retained(self):
        items = self.engine.items()
        items[0]["Mounts"].append({"Type": "volume", "Name": "original-volume-id", "Destination": "/data/configdb"})
        config = copy.deepcopy(self.engine.config)
        deploy.verify_mounts(config, items)
        self.assertEqual(deploy.mounted_sources(config)[deploy.SERVICES[0]]["/data/configdb"],
                         ("volume", "original-volume-id"))
        self.assertTrue(next(iter(config["volumes"].values()))["external"])

    def test_readiness_executes_probes_and_rejects_probe_failure(self):
        deploy.ready("original-project", timeout=0)
        self.assertEqual(sum(call[0] == "exec" for call in self.engine.calls), 3)
        self.engine.status = "exited"
        with self.assertRaisesRegex(deploy.DeployError, "timed out"):
            deploy.ready("original-project", timeout=0)

    def test_pull_only_does_not_apply_or_change_running_images(self):
        self.run_action("pull")
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])
        self.assertFalse(any("up" in call for call in self.engine.calls))

    def test_interrupted_apply_leaves_manual_recovery_available(self):
        with patch.object(self.deployment, "apply", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_action()
        self.assertTrue(self.deployment.state["pending"])
        deploy.Deployment(self.state_root).run("rollback", "", self.directory)
        self.assertEqual(self.images(), ["sha256:old0", "sha256:old1", "sha256:old2"])

    def test_unmounted_uploads_block_recreation(self):
        def with_uploads(*args, **kwargs):
            if args[0] == "exec" and args[1] == deploy.SERVICES[1]:
                return "present"
            return self.engine(*args, **kwargs)
        with patch.object(deploy, "docker", side_effect=with_uploads):
            with self.assertRaisesRegex(deploy.DeployError, "unmounted uploads"):
                self.run_action()
        self.assertFalse(any("up" in call or "pull" in call for call in self.engine.calls))

    def test_successful_secret_is_retained_and_rollback_restores_old_source(self):
        with patch.dict(os.environ, {"DOCKER_COMPOSE_ENV": "PASSWORD='new$literal'\n"}):
            self.run_action()
        current = self.deployment.record(self.deployment.state["current"])
        self.assertEqual(current["env_text"], "PASSWORD='new$literal'\n")
        self.run_action("rollback")
        restored = self.deployment.record(self.deployment.state["current"])
        self.assertEqual(restored["env_text"], "PASSWORD=old$literal\n")

    @unittest.skipUnless(shutil.which("node"), "Node CLI unavailable")
    def test_empty_upload_placeholder_allows_update(self):
        uploads = self.directory / "uploads"
        uploads.mkdir()
        (uploads / ".gitkeep").touch()

        def with_placeholder(*args, **kwargs):
            if args[0] == "exec" and deploy.UPLOADS_PROBE in args:
                return subprocess.run(["node", "-e", deploy.UPLOADS_PROBE, str(uploads)],
                                      text=True, capture_output=True, check=True).stdout
            return self.engine(*args, **kwargs)

        with patch.object(deploy, "docker", side_effect=with_placeholder):
            self.run_action()
        self.assertEqual(self.images(), ["sha256:new0", "sha256:new1", "sha256:new2"])


@unittest.skipUnless(shutil.which("node"), "Node CLI unavailable; actual uploads probe checks skipped")
class UploadProbeTests(unittest.TestCase):
    def probe(self, path):
        return subprocess.run(["node", "-e", deploy.UPLOADS_PROBE, str(path)],
                              text=True, capture_output=True, check=True).stdout

    def test_tracked_upload_directory_has_only_placeholder(self):
        path = Path(__file__).resolve().parents[1] / "backend/src/uploads"
        self.assertEqual(self.probe(path), "empty")

    def test_nested_empty_placeholders_do_not_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitkeep").touch()
            (root / "nested").mkdir()
            (root / "nested/.gitkeep").touch()
            self.assertEqual(self.probe(root), "empty")

    def test_real_hidden_nested_and_nonempty_placeholder_files_block(self):
        for name in ["report.pdf", ".hidden", ".gitkeep", "nested/report.pdf"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                file = root / name
                file.parent.mkdir(exist_ok=True)
                file.write_text("uploaded content")
                self.assertEqual(self.probe(root), "present")

    def test_symlink_named_gitkeep_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitkeep").symlink_to(root / "missing")
            self.assertEqual(self.probe(root), "present")


@unittest.skipUnless(shutil.which("docker"), "Docker CLI unavailable; parsing integration check skipped")
class ComposeParsingTests(unittest.TestCase):
    def test_real_compose_preserves_literal_environment_and_mount_paths(self):
        # `config` only parses files; it never contacts the Docker daemon.
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"SUDO_PASSWORD": ""}):
            root = Path(directory)
            env = root / "test.env"
            env.write_text("PASSWORD='literal$and$$dollars'\n")
            source = root / "source.json"
            source.write_text(json.dumps({"services": {"test": {
                "image": "unused:test", "env_file": [str(env)], "volumes": [str(root) + ":/data"]}}}))
            meta = {"project": "ris-validation", "directory": str(root)}
            config = deploy.render(meta, [source], env)
            self.assertEqual(config["services"]["test"]["environment"]["PASSWORD"], "literal$and$$dollars")
            recovery = root / "recovery"
            recovery.mkdir()
            _, record = deploy.Deployment(recovery).store(meta, config)
            restored = deploy.render(meta, [record["file"]])
            self.assertEqual(restored["services"]["test"]["environment"]["PASSWORD"], "literal$and$$dollars")
            self.assertEqual(deploy.mounted_sources(restored), deploy.mounted_sources(config))


if __name__ == "__main__":
    unittest.main()
