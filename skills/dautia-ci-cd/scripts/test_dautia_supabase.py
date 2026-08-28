#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("dautia_supabase.py")
spec = importlib.util.spec_from_file_location("dautia_supabase", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def write_contract(root: Path, project_ref: str = "abcdefghijklmnopqrst") -> None:
    (root / "supabase").mkdir(parents=True)
    (root / "delivery.yaml").write_text(
        json.dumps(
            {
                "provider_projects": [
                    {
                        "provider": "supabase",
                        "environment": "staging",
                        "project_ref": project_ref,
                        "workdir": ".",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class DautiaSupabaseTests(unittest.TestCase):
    def test_linux_credential_set_writes_registry_without_keychain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "credentials.json"
            args = Namespace(project_ref="abcdefghijklmnopqrst")
            with (
                patch.dict(
                    os.environ,
                    {"DAUTIA_SUPABASE_CREDENTIAL_FILE": str(registry)},
                    clear=True,
                ),
                patch.object(module.platform, "system", return_value="Linux"),
                patch.object(module.getpass, "getpass", side_effect=["test-password", "test-password"]),
                patch.object(module, "keychain_set") as keychain_set,
            ):
                self.assertEqual(0, module.cmd_credential_set(args))
                keychain_set.assert_not_called()
                self.assertEqual(
                    "test-password",
                    module.credential_registry_get("abcdefghijklmnopqrst"),
                )
            self.assertEqual(0o600, registry.stat().st_mode & 0o777)

    def test_protected_registry_round_trip_avoids_keychain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "credentials.json"
            with patch.dict(
                os.environ,
                {"DAUTIA_SUPABASE_CREDENTIAL_FILE": str(registry)},
                clear=True,
            ):
                module.credential_registry_set(
                    "abcdefghijklmnopqrst", "test-password"
                )
                with patch.object(module, "keychain_get") as keychain_get:
                    self.assertEqual(
                        "test-password",
                        module.require_password("abcdefghijklmnopqrst", "staging"),
                    )
                    keychain_get.assert_not_called()
            self.assertEqual(0o600, registry.stat().st_mode & 0o777)

    def test_insecure_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "credentials.json"
            registry.write_text(
                json.dumps({"abcdefghijklmnopqrst": "test-password"}),
                encoding="utf-8",
            )
            registry.chmod(0o644)
            with patch.dict(
                os.environ,
                {"DAUTIA_SUPABASE_CREDENTIAL_FILE": str(registry)},
                clear=True,
            ):
                with self.assertRaisesRegex(module.SetupError, "permisos 0600"):
                    module.credential_registry_get("abcdefghijklmnopqrst")

    def test_keychain_is_imported_once_into_protected_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "credentials.json"
            with (
                patch.dict(
                    os.environ,
                    {"DAUTIA_SUPABASE_CREDENTIAL_FILE": str(registry)},
                    clear=True,
                ),
                patch.object(module, "keychain_get", return_value="test-password") as keychain_get,
            ):
                self.assertEqual(
                    "test-password",
                    module.require_password("abcdefghijklmnopqrst", "staging"),
                )
                self.assertEqual(
                    "test-password",
                    module.require_password("abcdefghijklmnopqrst", "staging"),
                )
                keychain_get.assert_called_once()

    def test_cli_environment_uses_secure_fallback_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token_file = Path(directory) / "access-token"
            token_file.write_text("sbp_test-token\n", encoding="utf-8")
            token_file.chmod(0o600)
            with (
                patch.object(module, "ACCESS_TOKEN_FILE", token_file),
                patch.dict(os.environ, {}, clear=True),
            ):
                child_env = module.cli_environment()
            self.assertEqual("sbp_test-token", child_env["SUPABASE_ACCESS_TOKEN"])

    def test_insecure_access_token_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token_file = Path(directory) / "access-token"
            token_file.write_text("sbp_test-token\n", encoding="utf-8")
            token_file.chmod(0o644)
            with (
                patch.object(module, "ACCESS_TOKEN_FILE", token_file),
                patch.dict(os.environ, {}, clear=True),
            ):
                with self.assertRaisesRegex(module.SetupError, "permisos 0600"):
                    module.cli_environment()

    def test_resolves_declared_target_and_matching_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            temp = root / "supabase" / ".temp"
            temp.mkdir()
            (temp / "project-ref").write_text("abcdefghijklmnopqrst\n", encoding="utf-8")
            target = module.resolve_target(root, "staging")
            self.assertEqual("abcdefghijklmnopqrst", target.project_ref)
            self.assertEqual("delivery.yaml", target.source)

    def test_contradictory_link_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            temp = root / "supabase" / ".temp"
            temp.mkdir()
            (temp / "project-ref").write_text("zyxwvutsrqponmlkjihg\n", encoding="utf-8")
            with self.assertRaisesRegex(module.SetupError, "Identidad contradictoria"):
                module.resolve_target(root, "staging")

    def test_contradictory_link_can_be_resolved_for_bootstrap_or_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            temp = root / "supabase" / ".temp"
            temp.mkdir()
            (temp / "project-ref").write_text("zyxwvutsrqponmlkjihg\n", encoding="utf-8")
            target = module.resolve_target(root, "staging", require_link_match=False)
            self.assertEqual("abcdefghijklmnopqrst", target.project_ref)

    def test_resolves_multi_environment_database_change_control_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "supabase").mkdir()
            (root / "delivery.yaml").write_text(
                json.dumps(
                    {
                        "database_change_control": {
                            "provider": "supabase",
                            "targets": {
                                "staging": {"project_ref": "abcdefghijklmnopqrst"},
                                "production": {"project_ref": "zyxwvutsrqponmlkjihg"},
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            target = module.resolve_target(root, "production", require_link_match=False)
            self.assertEqual("zyxwvutsrqponmlkjihg", target.project_ref)
            self.assertEqual("database_change_control", target.source)

    def test_legacy_single_link_is_supported_during_migration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "delivery.yaml").write_text("{}", encoding="utf-8")
            temp = root / "apps" / "api" / "supabase" / ".temp"
            temp.mkdir(parents=True)
            (temp / "project-ref").write_text("abcdefghijklmnopqrst\n", encoding="utf-8")
            target = module.resolve_target(root, "staging")
            self.assertEqual("legacy-link", target.source)
            self.assertEqual((root / "apps" / "api").resolve(), target.workdir)

    def test_matching_env_password_can_be_imported_without_printing_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            env = root / ".env.local"
            env.write_text(
                'SUPABASE_PROJECT_ID="abcdefghijklmnopqrst"\n'
                'SUPABASE_DB_PASSWORD="not-printed-secret"\n',
                encoding="utf-8",
            )
            target = module.resolve_target(root, "staging")
            password, source = module.existing_env_password(target)
            self.assertEqual("not-printed-secret", password)
            self.assertEqual(env.resolve(), source)

    def test_mismatched_env_is_not_imported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            (root / ".env.local").write_text(
                'SUPABASE_PROJECT_ID="zyxwvutsrqponmlkjihg"\n'
                'SUPABASE_DB_PASSWORD="wrong-target"\n',
                encoding="utf-8",
            )
            target = module.resolve_target(root, "staging")
            self.assertEqual((None, None), module.existing_env_password(target))

    def test_production_env_file_can_be_imported_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            env = root / ".env.production.local"
            env.write_text(
                "SUPABASE_PROJECT_REF=abcdefghijklmnopqrst\n"
                "SUPABASE_DB_PASSWORD=temporary-secret\n",
                encoding="utf-8",
            )
            target = module.resolve_target(root, "staging")
            password, source = module.existing_env_password(target)
            self.assertEqual("temporary-secret", password)
            self.assertEqual(env.resolve(), source)

    def test_local_migration_creation_does_not_require_db_password(self) -> None:
        self.assertFalse(module.command_needs_password(["migration", "new", "example"]))
        self.assertTrue(module.command_needs_password(["db", "push", "--dry-run"]))
        self.assertTrue(module.command_needs_password(["migration", "list", "--linked"]))

    def test_run_auto_links_fresh_worktree_without_interaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            calls: list[list[str]] = []

            def fake_run(command, **kwargs):
                calls.append(command)
                if "link" in command:
                    self.assertIs(module.subprocess.DEVNULL, kwargs["stdin"])
                    self.assertTrue(kwargs["capture_output"])
                    self.assertIn("--yes", command)
                    self.assertEqual("test-password", kwargs["env"]["SUPABASE_DB_PASSWORD"])
                    temp = root / "supabase" / ".temp"
                    temp.mkdir(parents=True)
                    (temp / "project-ref").write_text(
                        "abcdefghijklmnopqrst\n", encoding="utf-8"
                    )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            args = Namespace(
                root=str(root),
                environment="staging",
                command=["--", "migration", "list", "--linked"],
            )
            with (
                patch.object(module, "require_password", return_value="test-password"),
                patch.object(module.subprocess, "run", side_effect=fake_run),
            ):
                self.assertEqual(0, module.cmd_run(args))

            self.assertEqual(2, len(calls))
            self.assertIn("link", calls[0])
            self.assertEqual("migration", calls[1][-3])

    def test_run_rejects_manual_link_before_cli_can_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            args = Namespace(
                root=str(root),
                environment="staging",
                command=["--", "link", "--project-ref", "abcdefghijklmnopqrst"],
            )
            with self.assertRaisesRegex(module.SetupError, "No uses `supabase link`"):
                module.cmd_run(args)

    def test_activate_links_only_the_explicit_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "supabase" / ".temp").mkdir(parents=True)
            (root / "supabase" / ".temp" / "project-ref").write_text(
                "abcdefghijklmnopqrst\n", encoding="utf-8"
            )
            (root / "delivery.yaml").write_text(
                json.dumps(
                    {
                        "database_change_control": {
                            "targets": {
                                "staging": {"project_ref": "abcdefghijklmnopqrst"},
                                "production": {"project_ref": "zyxwvutsrqponmlkjihg"},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            def fake_run(command, **kwargs):
                self.assertIn("link", command)
                self.assertEqual("zyxwvutsrqponmlkjihg", command[-2])
                self.assertEqual("--yes", command[-1])
                self.assertEqual("test-password", kwargs["env"]["SUPABASE_DB_PASSWORD"])
                self.assertIs(module.subprocess.DEVNULL, kwargs["stdin"])
                self.assertTrue(kwargs["capture_output"])
                self.assertEqual(30, kwargs["timeout"])
                (root / "supabase" / ".temp" / "project-ref").write_text(
                    "zyxwvutsrqponmlkjihg\n", encoding="utf-8"
                )
                return SimpleNamespace(returncode=0)

            args = Namespace(root=str(root), environment="production")
            with (
                patch.object(module, "require_password", return_value="test-password"),
                patch.object(module.subprocess, "run", side_effect=fake_run),
            ):
                self.assertEqual(0, module.cmd_activate(args))

    def test_activate_is_a_noop_when_the_checkout_is_already_linked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_contract(root)
            temp = root / "supabase" / ".temp"
            temp.mkdir()
            (temp / "project-ref").write_text(
                "abcdefghijklmnopqrst\n", encoding="utf-8"
            )
            args = Namespace(root=str(root), environment="staging")
            with (
                patch.object(module, "require_password", return_value="test-password"),
                patch.object(module.subprocess, "run") as run,
            ):
                self.assertEqual(0, module.cmd_activate(args))
                run.assert_not_called()

    def test_keychain_set_answers_prompts_from_the_controlling_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake_security = Path(directory) / "security"
            fake_security.write_text(
                "#!/bin/sh\n"
                "printf 'password data for new item: '\n"
                "IFS= read -r first\n"
                "printf 'retype password for new item: '\n"
                "IFS= read -r second\n"
                "[ \"$first\" = \"test-password\" ] && [ \"$second\" = \"test-password\" ]\n",
                encoding="utf-8",
            )
            fake_security.chmod(0o700)
            with patch.dict(os.environ, {"DAUTIA_SECURITY_BIN": str(fake_security)}):
                module.keychain_set("abcdefghijklmnopqrst", "test-password")


if __name__ == "__main__":
    unittest.main()
