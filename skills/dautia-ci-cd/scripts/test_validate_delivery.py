#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_delivery.py")
ASSET = Path(__file__).parents[1] / "assets" / "delivery.yaml"
spec = importlib.util.spec_from_file_location("validate_delivery", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(validator)


def active_v2() -> dict:
    return {
        "schema_version": 2,
        "project": "example",
        "product_topology": "multi-codebase",
        "repository_layout": "monorepo",
        "configuration_status": "active",
        "production_enabled": True,
        "repositories": [
            {"id": "product", "path": ".", "integration_branch": "dev"},
        ],
        "codebases": [
            {
                "id": "web",
                "repository": "product",
                "path": "apps/web",
                "kind": "web",
                "status": "active",
                "delivery_target": "vercel:web",
            },
            {
                "id": "ios",
                "repository": "product",
                "path": "apps/ios",
                "kind": "ios",
                "status": "active",
                "delivery_target": "app-store:ios",
            },
        ],
        "environments": {
            "integration": {
                "branch": "dev",
                "state": "observed",
                "deploy_enabled": False,
                "target": "local-ci",
            },
            "staging": {
                "branch": "staging",
                "state": "observed",
                "deploy_enabled": True,
                "target": "provider:staging",
            },
            "production": {
                "branch": "main",
                "state": "observed",
                "deploy_enabled": True,
                "target": "provider:production",
            },
        },
        "required_checks": {
            "integration": ["contracts", "ci-required"],
            "staging": ["contracts", "promotion-gate"],
            "production": ["contracts", "release-gate"],
        },
        "rollback_refs": ["docs/runbooks/release.md"],
    }


def active_v1() -> dict:
    return {
        "schema_version": 1,
        "project": "legacy",
        "topology": "single-repo",
        "configuration_status": "active",
        "production_enabled": False,
        "branches": {
            "integration": {"name": "dev", "state": "observed", "bootstrap_required": False},
            "staging": {"name": "staging", "state": "observed", "bootstrap_required": False},
            "production": {"name": "main", "state": "observed", "bootstrap_required": False},
        },
        "components": [
            {
                "id": "web",
                "path": ".",
                "kind": "web",
                "status": "active",
                "platform": "vercel",
                "delivery_target": "project:web",
            },
        ],
        "data": {
            "active_dev_db": "local",
            "active_test_target": "unit",
            "recommended_dev_db": "wsl",
            "wsl_status": "available",
        },
        "environments": {
            role: {
                "lifecycle_environment": role,
                "provider_target": f"provider:{role}",
                "deploy_enabled": False,
            }
            for role in validator.ROLES
        },
        "required_checks": {
            "integration": ["contracts", "ci-required"],
            "staging": ["contracts", "promotion-gate"],
            "production": ["contracts", "release-gate"],
        },
        "qa_defaults": {
            "risk_class": "medium",
            "affected_contracts": ["delivery"],
            "required_test_dimensions": ["unit"],
            "excluded_test_dimensions": ["ui"],
            "target_environment": "local",
            "expected_duration": "10m",
            "escalation_conditions": ["validation failure"],
        },
        "promotion_identity": {
            "integration_to_staging": {"source_branch": "dev", "target_branch": "staging"},
            "staging_to_production": {"source_branch": "staging", "target_branch": "main"},
        },
        "rollback_refs": ["docs/runbooks/release.md"],
    }


class DeliveryValidationTests(unittest.TestCase):
    def test_v2_minimal_draft_is_valid(self) -> None:
        self.assertEqual([], validator.validate(json.loads(ASSET.read_text())))

    def test_legacy_v1_remains_valid(self) -> None:
        self.assertEqual([], validator.validate(active_v1()))

    def test_unknown_schema_is_rejected(self) -> None:
        data = active_v2()
        data["schema_version"] = 3
        self.assertIn("schema_version must equal 1 or 2", validator.validate(data))

    def test_v2_active_and_observed_branch_truth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "dev"], cwd=repo, check=True)
            subprocess.run(
                [
                    "git", "-c", "user.name=Test", "-c",
                    "user.email=test@example.invalid", "commit",
                    "--allow-empty", "-qm", "baseline",
                ],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "branch", "staging"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "main"], cwd=repo, check=True)
            self.assertEqual([], validator.validate(active_v2(), repo=repo))

    def test_require_active_rejects_draft(self) -> None:
        self.assertIn(
            "active configuration required",
            validator.validate(json.loads(ASSET.read_text()), require_active=True),
        )

    def test_active_missing_sections_is_rejected(self) -> None:
        data = json.loads(ASSET.read_text())
        data.update(configuration_status="active")
        data.pop("activation_blocked_reason")
        self.assertTrue(
            any("active configuration missing sections" in error for error in validator.validate(data))
        )

    def test_topology_and_layout_are_independent(self) -> None:
        data = active_v2()
        data["repository_layout"] = "multi-repo"
        self.assertIn("multi-repo requires at least two repositories", validator.validate(data))
        data = active_v2()
        data["product_topology"] = "single-codebase"
        self.assertIn("single-codebase requires exactly one codebase", validator.validate(data))

    def test_multi_repo_contract_accepts_independent_dev_repositories(self) -> None:
        data = active_v2()
        data["repository_layout"] = "multi-repo"
        data["repositories"] = [
            {"id": "web", "path": "web", "integration_branch": "dev"},
            {"id": "mobile", "path": "mobile", "integration_branch": "dev"},
        ]
        data["codebases"][0].update(repository="web", path=".")
        data["codebases"][1].update(repository="mobile", path=".")
        self.assertEqual([], validator.validate(data))

    def test_codebase_references_repository(self) -> None:
        data = active_v2()
        data["codebases"][0]["repository"] = "missing"
        self.assertTrue(any("does not reference" in error for error in validator.validate(data)))

    def test_integration_branch_must_match(self) -> None:
        data = active_v2()
        data["repositories"][0]["integration_branch"] = "develop"
        self.assertTrue(any("must match" in error for error in validator.validate(data)))

    def test_staging_may_be_the_declared_integration_branch(self) -> None:
        data = active_v2()
        data["repositories"][0]["integration_branch"] = "staging"
        data["environments"]["integration"]["branch"] = "staging"
        self.assertEqual([], validator.validate(data))

    def test_production_cannot_share_the_integration_branch(self) -> None:
        data = active_v2()
        data["environments"]["production"]["branch"] = "dev"
        self.assertTrue(
            any("must be unique" in error for error in validator.validate(data))
        )

    def test_planned_branch_disables_deploy(self) -> None:
        data = active_v2()
        data["environments"]["staging"].update(state="planned", deploy_enabled=True)
        self.assertTrue(any("planned branch" in error for error in validator.validate(data)))

    def test_project_specific_checks_are_valid(self) -> None:
        data = active_v2()
        data["required_checks"]["integration"] = [
            "contracts",
            "mobile-contracts",
            "android-required",
        ]
        self.assertEqual([], validator.validate(data))

    def test_supabase_provider_project_is_non_secret_stable_routing(self) -> None:
        data = active_v2()
        data["provider_projects"] = [
            {
                "provider": "supabase",
                "environment": "staging",
                "project_ref": "abcdefghijklmnopqrst",
                "workdir": ".",
            }
        ]
        self.assertEqual([], validator.validate(data))

    def test_provider_project_rejects_duplicates_and_unsafe_paths(self) -> None:
        data = active_v2()
        entry = {
            "provider": "supabase",
            "environment": "staging",
            "project_ref": "abcdefghijklmnopqrst",
            "workdir": "../supabase",
        }
        data["provider_projects"] = [entry, copy.deepcopy(entry)]
        errors = validator.validate(data)
        self.assertTrue(any("pairs must be unique" in error for error in errors))
        self.assertTrue(any("repository-relative" in error for error in errors))

    def test_draft_rejects_provider_project_routing(self) -> None:
        data = json.loads(ASSET.read_text())
        data["provider_projects"] = []
        self.assertIn(
            "draft configuration must not contain provider_projects",
            validator.validate(data),
        )

    def test_planned_environment_may_have_no_checks(self) -> None:
        data = active_v2()
        data["environments"]["staging"].update(state="planned", deploy_enabled=False)
        data["required_checks"]["staging"] = []
        self.assertEqual([], validator.validate(data))

    def test_observed_environment_requires_a_check(self) -> None:
        data = active_v2()
        data["required_checks"]["integration"] = []
        self.assertTrue(
            any("requires at least one check" in error for error in validator.validate(data))
        )

    def test_check_names_must_be_non_empty_strings(self) -> None:
        data = active_v2()
        data["required_checks"]["integration"] = ["contracts", "  "]
        self.assertTrue(
            any("must be a non-empty string" in error for error in validator.validate(data))
        )

    def test_disabled_production_rejects_enabled_deploy(self) -> None:
        data = active_v2()
        data["production_enabled"] = False
        self.assertIn(
            "production_disabled requires production deployment disabled",
            validator.validate(data),
        )

    def test_duplicate_codebase_paths_are_rejected(self) -> None:
        data = active_v2()
        duplicate = copy.deepcopy(data["codebases"][0])
        duplicate["id"] = "duplicate"
        data["codebases"].append(duplicate)
        self.assertTrue(any("repository/path pairs" in error for error in validator.validate(data)))

    def test_secret_like_key_and_values(self) -> None:
        for mutation in (
            lambda data: data.update(api_token="value"),
            lambda data: data["rollback_refs"].append("postgres://user:password@host/db"),
            lambda data: data["rollback_refs"].append("ghp_1234567890abcdef"),
        ):
            data = active_v2()
            mutation(data)
            self.assertTrue(
                any(
                    "credential-like" in error or "secret-like" in error
                    for error in validator.validate(data)
                )
            )


if __name__ == "__main__":
    unittest.main()
