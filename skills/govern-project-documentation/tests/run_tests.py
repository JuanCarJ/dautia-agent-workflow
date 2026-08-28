#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def run(*args: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True, text=True, check=False)


def init_repo(path: Path, commit: bool = True) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run("git", "init", "-b", "main", path)
    run("git", "-C", path, "config", "user.email", "tests@example.invalid")
    run("git", "-C", path, "config", "user.name", "Skill Tests")
    if commit:
        (path / ".gitkeep").write_text("", encoding="utf-8")
        run("git", "-C", path, "add", ".gitkeep")
        run("git", "-C", path, "commit", "-m", "test fixture")


class TemporaryCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="govern-docs-test-")
        self.base = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()


class AuditTests(TemporaryCase):
    script = SCRIPTS / "audit_workspace.sh"

    def audit(self, path: Path) -> subprocess.CompletedProcess[str]:
        return run("bash", self.script, path)

    def test_01_no_git_warning(self) -> None:
        result = self.audit(self.base)
        self.assertIn("git_repositories=0", result.stdout)

    def test_02_single_repo(self) -> None:
        init_repo(self.base / "app")
        result = self.audit(self.base / "app")
        self.assertIn("git_repositories=1", result.stdout)

    def test_03_nested_repositories(self) -> None:
        init_repo(self.base / "parent")
        init_repo(self.base / "parent" / "child")
        result = self.audit(self.base / "parent")
        self.assertIn("git_repositories=2", result.stdout)

    def test_04_external_docs_warning(self) -> None:
        (self.base / "docs").mkdir()
        (self.base / "docs" / "README.md").write_text("docs", encoding="utf-8")
        init_repo(self.base / "app")
        result = self.audit(self.base)
        self.assertIn("versioned_by=NONE warning=normative-risk", result.stdout)

    def test_05_generated_docs_pruned(self) -> None:
        init_repo(self.base / "app")
        generated = self.base / "app" / "node_modules" / "pkg" / "docs"
        generated.mkdir(parents=True)
        (generated / "x.md").write_text("x", encoding="utf-8")
        result = self.audit(self.base / "app")
        self.assertNotIn("node_modules", result.stdout)

    def test_06_missing_agents(self) -> None:
        init_repo(self.base / "app")
        result = self.audit(self.base / "app")
        self.assertIn("agents=missing", result.stdout)

    def test_07_present_agents(self) -> None:
        init_repo(self.base / "app")
        (self.base / "app" / "AGENTS.md").write_text("rules", encoding="utf-8")
        result = self.audit(self.base / "app")
        self.assertIn("agents=present", result.stdout)

    def test_08_dirty_counts(self) -> None:
        init_repo(self.base / "app")
        (self.base / "app" / "new.txt").write_text("new", encoding="utf-8")
        result = self.audit(self.base / "app")
        self.assertIn("untracked=1", result.stdout)

    def test_09_detached_head(self) -> None:
        init_repo(self.base / "app")
        run("git", "-C", self.base / "app", "checkout", "--detach", "HEAD")
        result = self.audit(self.base / "app")
        self.assertIn("branch=DETACHED", result.stdout)

    def test_10_secret_content_not_printed(self) -> None:
        init_repo(self.base / "app")
        (self.base / "app" / ".env").write_text("TOKEN=super-secret-value", encoding="utf-8")
        result = self.audit(self.base / "app")
        self.assertNotIn("super-secret-value", result.stdout + result.stderr)

    def test_10b_git_worktree_is_detected(self) -> None:
        repo = self.base / "app"
        worktree = self.base / "worktree"
        init_repo(repo)
        created = run("git", "-C", repo, "worktree", "add", worktree, "-b", "docs/test")
        self.assertEqual(created.returncode, 0, created.stderr)
        result = self.audit(worktree)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("git_repositories=1", result.stdout)
        self.assertIn("branch=docs/test", result.stdout)


class ManifestTests(TemporaryCase):
    script = SCRIPTS / "validate_manifest.py"

    def write(self, data: object, name: str = "manifest.yaml") -> Path:
        path = self.base / name
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    def valid_workspace(self) -> dict[str, object]:
        return {
            "version": 1,
            "project": {"id": "demo", "topology": "multi-repo"},
            "repositories": [
                {"id": "web", "path": "../web", "role": "web", "base_branch": "dev", "allowed_flows": ["feature/* -> dev"]}
            ],
        }

    def test_11_valid_workspace(self) -> None:
        result = run("python3", self.script, self.write(self.valid_workspace()))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_12_invalid_topology(self) -> None:
        data = self.valid_workspace(); data["project"]["topology"] = "folder"  # type: ignore[index]
        result = run("python3", self.script, self.write(data))
        self.assertEqual(result.returncode, 1)

    def test_13_duplicate_repo_id(self) -> None:
        data = self.valid_workspace(); data["repositories"].append(dict(data["repositories"][0]))  # type: ignore[union-attr,index]
        result = run("python3", self.script, self.write(data))
        self.assertIn("duplicate id", result.stderr)

    def test_14_missing_repo_path(self) -> None:
        data = self.valid_workspace(); del data["repositories"][0]["path"]  # type: ignore[index]
        result = run("python3", self.script, self.write(data))
        self.assertIn("path", result.stderr)

    def test_15_valid_initiative(self) -> None:
        data = {
            "id": "INIT-1", "name": "Demo", "lifecycle": "design", "authority": "governance",
            "canonical": {"functional": "functional.md"},
            "implementation_entry_gate": {"approved": False, "criteria": ["scope approved"]},
        }
        result = run("python3", self.script, self.write(data), "--kind", "initiative")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_16_design_cannot_be_approved(self) -> None:
        data = {
            "id": "INIT-1", "name": "Demo", "lifecycle": "design", "authority": "governance",
            "canonical": {"functional": "functional.md"},
            "implementation_entry_gate": {"approved": True, "criteria": ["scope approved"]},
        }
        result = run("python3", self.script, self.write(data), "--kind", "initiative")
        self.assertIn("cannot have", result.stderr)


class TraceabilityTests(TemporaryCase):
    script = SCRIPTS / "validate_traceability.py"
    header = "| Requisito | Estado | Repos | PR/commits | Pruebas | Ambiente | Release |\n| --- | --- | --- | --- | --- | --- | --- |\n"

    def validate(self, body: str) -> subprocess.CompletedProcess[str]:
        path = self.base / "trace.md"
        path.write_text(self.header + body, encoding="utf-8")
        return run("python3", self.script, path)

    def test_17_valid_planned(self) -> None:
        result = self.validate("| RF-001 | planned | — | — | — | — | — |\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_18_valid_closed(self) -> None:
        result = self.validate("| RF-001 | closed | web | PR-1 | TEST-1 | staging | REL-20260709-01 |\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_19_closed_missing_evidence(self) -> None:
        result = self.validate("| RF-001 | closed | — | — | — | — | — |\n")
        self.assertIn("closed item missing", result.stderr)

    def test_20_duplicate_requirement(self) -> None:
        result = self.validate("| RF-001 | planned | — | — | — | — | — |\n| RF-001 | planned | — | — | — | — | — |\n")
        self.assertIn("duplicate", result.stderr)

    def test_21_invalid_requirement_id(self) -> None:
        result = self.validate("| feature-one | planned | — | — | — | — | — |\n")
        self.assertIn("invalid requirement", result.stderr)


class ScaffoldTests(TemporaryCase):
    script = SCRIPTS / "scaffold_governance.py"

    def test_22_dry_run_no_write(self) -> None:
        init_repo(self.base / "repo")
        result = run("python3", self.script, "governance", self.base / "repo", "--project", "Demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.base / "repo" / "AGENTS.md").exists())

    def test_23_write_creates_files(self) -> None:
        init_repo(self.base / "repo")
        result = run("python3", self.script, "governance", self.base / "repo", "--project", "Demo", "--write")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / "repo" / "AGENTS.md").exists())

    def test_24_conflict_rejected(self) -> None:
        init_repo(self.base / "repo")
        (self.base / "repo" / "AGENTS.md").write_text("existing", encoding="utf-8")
        result = run("python3", self.script, "governance", self.base / "repo", "--write")
        self.assertEqual(result.returncode, 1)

    def test_25_initiative_replaces_id(self) -> None:
        init_repo(self.base / "repo")
        result = run("python3", self.script, "initiative", self.base / "repo", "--initiative-id", "DEMO-01", "--initiative-name", "Future Demo", "--write")
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.base / "repo" / "docs" / "initiatives" / "DEMO-01" / "initiative.yaml"
        self.assertIn("DEMO-01", path.read_text(encoding="utf-8"))

    def test_26_non_git_rejected(self) -> None:
        result = run("python3", self.script, "governance", self.base / "plain")
        self.assertEqual(result.returncode, 2)

    def test_31_symlink_destination_rejected(self) -> None:
        init_repo(self.base / "repo")
        target = self.base / "repo" / "real"; target.mkdir()
        link = self.base / "repo" / "linked"; link.symlink_to(target, target_is_directory=True)
        result = run("python3", self.script, "governance", link)
        self.assertEqual(result.returncode, 2)

    def test_32_unsafe_initiative_id_rejected(self) -> None:
        init_repo(self.base / "repo")
        result = run("python3", self.script, "initiative", self.base / "repo", "--initiative-id", "../../escape")
        self.assertEqual(result.returncode, 2)


class LockTests(TemporaryCase):
    script = SCRIPTS / "build_workspace_lock.py"

    def manifest(self, repo: Path) -> Path:
        path = self.base / "workspace.yaml"
        path.write_text(yaml.safe_dump({
            "project": {"id": "demo", "topology": "multi-repo"},
            "repositories": [{"id": "app", "path": os.path.relpath(repo, self.base), "role": "app", "base_branch": "main"}],
        }, sort_keys=False), encoding="utf-8")
        return path

    def test_27_draft_dirty_allowed(self) -> None:
        repo = self.base / "app"; init_repo(repo); (repo / "dirty.txt").write_text("x", encoding="utf-8")
        result = run("python3", self.script, self.manifest(repo))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dirty: true", result.stdout)

    def test_28_approved_dirty_fails(self) -> None:
        repo = self.base / "app"; init_repo(repo); (repo / "dirty.txt").write_text("x", encoding="utf-8")
        result = run("python3", self.script, self.manifest(repo), "--status", "approved")
        self.assertEqual(result.returncode, 1)

    def test_29_approved_clean_succeeds(self) -> None:
        repo = self.base / "app"; init_repo(repo)
        result = run("python3", self.script, self.manifest(repo), "--status", "approved")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status: approved", result.stdout)

    def test_30_output_dry_run_does_not_write(self) -> None:
        repo = self.base / "app"; init_repo(repo); output = self.base / "lock.yaml"
        result = run("python3", self.script, self.manifest(repo), "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(output.exists())


class GovernanceGateTests(TemporaryCase):
    links = SCRIPTS / "check_markdown_links.py"
    branch = SCRIPTS / "validate_branch_flow.py"
    sensitive = SCRIPTS / "scan_sensitive_sources.py"

    def test_33_valid_relative_link(self) -> None:
        (self.base / "target.md").write_text("target", encoding="utf-8")
        (self.base / "index.md").write_text("[target](target.md)", encoding="utf-8")
        result = run("python3", self.links, self.base)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_34_broken_relative_link(self) -> None:
        (self.base / "index.md").write_text("[missing](missing.md)", encoding="utf-8")
        result = run("python3", self.links, self.base)
        self.assertEqual(result.returncode, 1)

    def test_35_absolute_link_rejected(self) -> None:
        (self.base / "index.md").write_text("[local](/tmp/local.md)", encoding="utf-8")
        result = run("python3", self.links, self.base)
        self.assertIn("machine-local", result.stderr)

    def flow_manifest(self) -> Path:
        path = self.base / "workspace.yaml"
        path.write_text(yaml.safe_dump({
            "repositories": [{"id": "web", "path": ".", "role": "web", "base_branch": "dev", "allowed_flows": ["feature/* -> dev", "dev -> staging", "staging -> main"]}]
        }, sort_keys=False), encoding="utf-8")
        return path

    def test_36_allowed_branch_flow(self) -> None:
        result = run("python3", self.branch, self.flow_manifest(), "web", "feature/demo", "dev")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_37_disallowed_branch_flow(self) -> None:
        result = run("python3", self.branch, self.flow_manifest(), "web", "feature/demo", "main")
        self.assertEqual(result.returncode, 1)

    def test_38_sensitive_unignored_fails_without_content(self) -> None:
        init_repo(self.base / "repo")
        secret = "TOKEN=must-not-appear"
        (self.base / "repo" / ".env").write_text(secret, encoding="utf-8")
        result = run("python3", self.sensitive, self.base / "repo")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_39_sensitive_ignored_passes(self) -> None:
        init_repo(self.base / "repo")
        (self.base / "repo" / ".gitignore").write_text(".env\n", encoding="utf-8")
        (self.base / "repo" / ".env").write_text("TOKEN=hidden", encoding="utf-8")
        result = run("python3", self.sensitive, self.base / "repo")
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
