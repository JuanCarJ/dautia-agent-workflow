#!/usr/bin/env python3
"""Validate a JSON-compatible YAML 1.2 DautIA delivery contract."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROLES = ("integration", "staging", "production")
BASE_KEYS = {"schema_version", "project", "topology", "configuration_status", "production_enabled"}
ACTIVE_KEYS = {"branches", "components", "data", "environments", "required_checks", "qa_defaults", "promotion_identity", "rollback_refs"}
TOP_KEYS = BASE_KEYS | ACTIVE_KEYS | {"activation_blocked_reason"}
QA_KEYS = {"risk_class", "affected_contracts", "required_test_dimensions", "excluded_test_dimensions", "target_environment", "expected_duration", "escalation_conditions"}
SECRET_KEY = re.compile(r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|credential|connection[_-]?string)", re.I)
SECRET_VALUE = re.compile(r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|\bBearer\s+[A-Za-z0-9._-]+|\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{8,}|(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s/:]+:[^\s/@]+@)", re.I)
V2_BASE_KEYS = {
    "schema_version", "project", "product_topology", "repository_layout",
    "configuration_status", "production_enabled",
}
V2_ACTIVE_KEYS = {
    "repositories", "codebases", "environments", "required_checks", "rollback_refs",
}
V2_TOP_KEYS = V2_BASE_KEYS | V2_ACTIVE_KEYS | {"activation_blocked_reason", "provider_projects"}


def load_contract(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"contract must use JSON-compatible YAML 1.2: {exc}") from exc


def duplicates(values: list[Any]) -> bool:
    return len(values) != len(set(values))


def validate_role_checks(
    role_checks: Any,
    location: str,
    observed: bool,
    errors: list[str],
) -> None:
    if not isinstance(role_checks, list):
        errors.append(f"{location} must be an array")
        return
    if duplicates(role_checks):
        errors.append(f"{location} contains duplicates")
    for index, check in enumerate(role_checks):
        if not isinstance(check, str) or not check.strip():
            errors.append(f"{location}[{index}] must be a non-empty string")
    if observed and not role_checks:
        errors.append(f"{location} requires at least one check for an observed environment")


def scan_secrets(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_KEY.search(str(key)):
                errors.append(f"{location}.{key}: credential-like key is forbidden")
            scan_secrets(child, f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_secrets(child, f"{location}[{index}]", errors)
    elif isinstance(value, str) and SECRET_VALUE.search(value):
        errors.append(f"{location}: secret-like value is forbidden")


def git_branches(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"],
        cwd=repo, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError(f"cannot inspect git branches in {repo}: {result.stderr.strip()}")
    names = set(result.stdout.splitlines())
    names.update(name.split("/", 1)[1] for name in list(names) if "/" in name)
    return names


def validate_v1(contract: Any, repo: Path | None = None, require_active: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["contract root must be an object"]
    missing = BASE_KEYS - contract.keys()
    extra = contract.keys() - TOP_KEYS
    if missing: errors.append(f"missing top-level fields: {', '.join(sorted(missing))}")
    if extra: errors.append(f"unknown top-level fields: {', '.join(sorted(extra))}")
    if missing:
        scan_secrets(contract, "$", errors)
        return errors
    if contract["schema_version"] != 1: errors.append("schema_version must equal 1")
    if not isinstance(contract["project"], str) or not contract["project"]: errors.append("project must be a non-empty string")
    if contract["topology"] not in {"single-repo", "monorepo", "multi-repo"}: errors.append("topology must be single-repo, monorepo, or multi-repo")
    status = contract["configuration_status"]
    if status not in {"active", "draft"}: errors.append("configuration_status must be active or draft")
    if require_active and status != "active": errors.append("active configuration required")
    if not isinstance(contract["production_enabled"], bool): errors.append("production_enabled must be boolean")
    if status == "draft" and contract["production_enabled"] is not False: errors.append("draft configuration requires production_enabled false")
    if status == "draft" and ACTIVE_KEYS & contract.keys(): errors.append("draft configuration must not contain active delivery sections")
    if "activation_blocked_reason" in contract and (not isinstance(contract["activation_blocked_reason"], str) or not contract["activation_blocked_reason"]): errors.append("activation_blocked_reason must be a non-empty string")

    if status == "active":
        active_missing = ACTIVE_KEYS - contract.keys()
        if active_missing: errors.append(f"active configuration missing sections: {', '.join(sorted(active_missing))}")
    if not ACTIVE_KEYS.issubset(contract):
        scan_secrets(contract, "$", errors)
        return errors

    branches = contract["branches"]
    environments = contract["environments"]
    checks = contract["required_checks"]
    if not all(isinstance(item, dict) for item in (branches, environments, checks)):
        errors.append("branches, environments, and required_checks must be objects")
    else:
        for field, obj in (("branches", branches), ("environments", environments), ("required_checks", checks)):
            if set(obj) != set(ROLES): errors.append(f"{field} must contain exactly integration, staging, production")
        branch_names: list[str] = []
        observed = git_branches(repo) if repo else None
        for role in ROLES:
            branch = branches.get(role, {})
            env = environments.get(role, {})
            if set(branch) != {"name", "state", "bootstrap_required"}: errors.append(f"branches.{role} has invalid fields")
            name, state, bootstrap = branch.get("name"), branch.get("state"), branch.get("bootstrap_required")
            if not isinstance(name, str) or not name: errors.append(f"branches.{role}.name must be non-empty")
            else: branch_names.append(name)
            if state not in {"observed", "planned"}: errors.append(f"branches.{role}.state must be observed or planned")
            if not isinstance(bootstrap, bool): errors.append(f"branches.{role}.bootstrap_required must be boolean")
            if state == "observed" and bootstrap is not False: errors.append(f"branches.{role}: observed branch cannot require bootstrap")
            if state == "planned" and bootstrap is not True: errors.append(f"branches.{role}: planned branch must require bootstrap")
            if state == "planned" and env.get("deploy_enabled") is not False: errors.append(f"environments.{role}: planned branch requires deploy_enabled false")
            if observed is not None and state == "observed" and name not in observed: errors.append(f"branches.{role}: observed branch {name!r} not found in repo")
            validate_role_checks(
                checks.get(role),
                f"required_checks.{role}",
                state == "observed",
                errors,
            )
        if duplicates(branch_names): errors.append("branch names must be unique")

    components = contract["components"]
    if not isinstance(components, list): errors.append("components must be an array")
    else:
        component_keys = {"id", "path", "kind", "status", "platform", "delivery_target"}
        names = [item.get("id") for item in components if isinstance(item, dict)]
        paths = [item.get("path") for item in components if isinstance(item, dict)]
        if len(names) != len(components) or any(set(item) != component_keys for item in components if isinstance(item, dict)): errors.append("each component must contain exactly id, path, kind, status, platform, delivery_target")
        for index, item in enumerate(components):
            if not isinstance(item, dict): continue
            if item.get("status") not in {"active", "planned"}: errors.append(f"components[{index}].status must be active or planned")
            for key in ("id", "path", "kind", "platform", "delivery_target"):
                if not isinstance(item.get(key), str) or not item.get(key): errors.append(f"components[{index}].{key} must be non-empty")
            if item.get("path") == "unassigned" and item.get("status") != "planned": errors.append(f"components[{index}]: unassigned path is allowed only for planned components")
        concrete_paths = [path for path in paths if path != "unassigned"]
        if duplicates(names) or duplicates(concrete_paths): errors.append("component ids and assigned paths must be unique")

    data = contract["data"]
    if not isinstance(data, dict) or set(data) != {"active_dev_db", "active_test_target", "recommended_dev_db", "wsl_status"}: errors.append("data must contain exactly active_dev_db, active_test_target, recommended_dev_db, wsl_status")
    qa = contract["qa_defaults"]
    if not isinstance(qa, dict) or set(qa) != QA_KEYS: errors.append("qa_defaults must contain exactly the seven required fields")
    elif isinstance(qa.get("required_test_dimensions"), list) and isinstance(qa.get("excluded_test_dimensions"), list):
        if set(qa["required_test_dimensions"]) & set(qa["excluded_test_dimensions"]): errors.append("required and excluded test dimensions overlap")
        for key in ("affected_contracts", "required_test_dimensions", "excluded_test_dimensions", "escalation_conditions"):
            if not isinstance(qa.get(key), list): errors.append(f"qa_defaults.{key} must be an array")
            elif duplicates(qa[key]): errors.append(f"qa_defaults.{key} contains duplicates")

    promotion = contract["promotion_identity"]
    expected_promotion = {
        "integration_to_staging": (branches.get("integration", {}).get("name"), branches.get("staging", {}).get("name")),
        "staging_to_production": (branches.get("staging", {}).get("name"), branches.get("production", {}).get("name")),
    }
    if not isinstance(promotion, dict) or set(promotion) != set(expected_promotion): errors.append("promotion_identity must contain exactly both promotion steps")
    else:
        for step, (source, target) in expected_promotion.items():
            if promotion[step] != {"source_branch": source, "target_branch": target}: errors.append(f"promotion_identity.{step} contradicts branch roles")

    rollback = contract["rollback_refs"]
    if not isinstance(rollback, list): errors.append("rollback_refs must be an array")
    elif duplicates(rollback): errors.append("rollback_refs contains duplicates")

    if status == "active":
        placeholders = {"", "unconfirmed", "unknown", "tbd", "todo"}
        if not components: errors.append("active configuration requires at least one component")
        for key in ("active_dev_db", "active_test_target", "recommended_dev_db", "wsl_status"):
            if not isinstance(data.get(key), str) or data.get(key, "").strip().lower() in placeholders: errors.append(f"active configuration requires data.{key}")
        if not rollback: errors.append("active configuration requires rollback_refs")
        elif any(not isinstance(ref, str) or ref.strip().lower().startswith(("pending", "unconfirmed", "unknown", "tbd", "todo")) for ref in rollback): errors.append("active configuration requires concrete rollback_refs")
        if isinstance(qa, dict):
            for key in ("risk_class", "target_environment", "expected_duration"):
                if not isinstance(qa.get(key), str) or qa.get(key, "").strip().lower() in placeholders: errors.append(f"active configuration requires qa_defaults.{key}")
            for key in ("affected_contracts", "required_test_dimensions", "escalation_conditions"):
                if not qa.get(key): errors.append(f"active configuration requires qa_defaults.{key}")
        for role in ROLES:
            env = environments.get(role, {})
            if set(env) != {"lifecycle_environment", "provider_target", "deploy_enabled"}: errors.append(f"environments.{role} has invalid fields")
            if not isinstance(env.get("deploy_enabled"), bool): errors.append(f"environments.{role}.deploy_enabled must be boolean")
            for key in ("lifecycle_environment", "provider_target"):
                if not isinstance(env.get(key), str) or env.get(key, "").strip().lower() in placeholders: errors.append(f"active configuration requires environments.{role}.{key}")
        prod_enabled = contract["production_enabled"] is True
        if not prod_enabled and environments.get("production", {}).get("deploy_enabled") is not False: errors.append("production_disabled requires production environment deployment disabled")
        if prod_enabled:
            if environments.get("production", {}).get("deploy_enabled") is not True: errors.append("production_enabled requires production environment deployment enabled")
            if branches.get("production", {}).get("state") != "observed": errors.append("production deployment requires an observed production branch")
            if not rollback: errors.append("production deployment requires rollback refs")
    scan_secrets(contract, "$", errors)
    return errors


def validate_string(value: Any, location: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{location} must be a non-empty string")
        return False
    return True


def validate_v2(contract: Any, repo: Path | None = None, require_active: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["contract root must be an object"]

    missing = V2_BASE_KEYS - contract.keys()
    extra = contract.keys() - V2_TOP_KEYS
    if missing:
        errors.append(f"missing top-level fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unknown top-level fields: {', '.join(sorted(extra))}")
    if missing:
        scan_secrets(contract, "$", errors)
        return errors

    validate_string(contract["project"], "project", errors)
    if contract["product_topology"] not in {"single-codebase", "multi-codebase"}:
        errors.append("product_topology must be single-codebase or multi-codebase")
    if contract["repository_layout"] not in {"single-repo", "monorepo", "multi-repo"}:
        errors.append("repository_layout must be single-repo, monorepo, or multi-repo")
    status = contract["configuration_status"]
    if status not in {"active", "draft"}:
        errors.append("configuration_status must be active or draft")
    if require_active and status != "active":
        errors.append("active configuration required")
    if not isinstance(contract["production_enabled"], bool):
        errors.append("production_enabled must be boolean")
    if status == "draft":
        if contract["production_enabled"] is not False:
            errors.append("draft configuration requires production_enabled false")
        if V2_ACTIVE_KEYS & contract.keys():
            errors.append("draft configuration must not contain active delivery sections")
        if "provider_projects" in contract:
            errors.append("draft configuration must not contain provider_projects")
        validate_string(contract.get("activation_blocked_reason"), "activation_blocked_reason", errors)
    elif "activation_blocked_reason" in contract:
        errors.append("active configuration must not contain activation_blocked_reason")

    if status == "active":
        active_missing = V2_ACTIVE_KEYS - contract.keys()
        if active_missing:
            errors.append(f"active configuration missing sections: {', '.join(sorted(active_missing))}")
    if not V2_ACTIVE_KEYS.issubset(contract):
        scan_secrets(contract, "$", errors)
        return errors

    repositories = contract["repositories"]
    repository_ids: set[str] = set()
    repository_paths: list[str] = []
    if not isinstance(repositories, list) or not repositories:
        errors.append("repositories must be a non-empty array")
        repositories = []
    for index, item in enumerate(repositories):
        if not isinstance(item, dict) or set(item) != {"id", "path", "integration_branch"}:
            errors.append(f"repositories[{index}] must contain exactly id, path, integration_branch")
            continue
        for key in ("id", "path", "integration_branch"):
            validate_string(item.get(key), f"repositories[{index}].{key}", errors)
        repository_ids.add(item.get("id"))
        repository_paths.append(item.get("path"))
    if len(repository_ids) != len(repositories):
        errors.append("repository ids must be unique")
    if len(set(repository_paths)) != len(repository_paths):
        errors.append("repository paths must be unique")
    layout = contract["repository_layout"]
    if layout in {"single-repo", "monorepo"} and len(repositories) != 1:
        errors.append(f"{layout} requires exactly one repository")
    if layout == "multi-repo" and len(repositories) < 2:
        errors.append("multi-repo requires at least two repositories")

    codebases = contract["codebases"]
    codebase_ids: list[str] = []
    assigned_paths: list[tuple[str, str]] = []
    if not isinstance(codebases, list) or not codebases:
        errors.append("codebases must be a non-empty array")
        codebases = []
    for index, item in enumerate(codebases):
        keys = {"id", "repository", "path", "kind", "status", "delivery_target"}
        if not isinstance(item, dict) or set(item) != keys:
            errors.append(
                f"codebases[{index}] must contain exactly id, repository, path, kind, status, delivery_target"
            )
            continue
        for key in ("id", "repository", "path", "kind", "status", "delivery_target"):
            validate_string(item.get(key), f"codebases[{index}].{key}", errors)
        codebase_ids.append(item.get("id"))
        if item.get("repository") not in repository_ids:
            errors.append(f"codebases[{index}].repository does not reference a repository id")
        if item.get("status") not in {"active", "planned"}:
            errors.append(f"codebases[{index}].status must be active or planned")
        if item.get("path") == "unassigned" and item.get("status") != "planned":
            errors.append(f"codebases[{index}]: unassigned path is allowed only for planned codebases")
        if item.get("path") != "unassigned":
            assigned_paths.append((item.get("repository"), item.get("path")))
    if duplicates(codebase_ids):
        errors.append("codebase ids must be unique")
    if duplicates(assigned_paths):
        errors.append("assigned codebase repository/path pairs must be unique")
    topology = contract["product_topology"]
    if topology == "single-codebase" and len(codebases) != 1:
        errors.append("single-codebase requires exactly one codebase")
    if topology == "multi-codebase" and len(codebases) < 2:
        errors.append("multi-codebase requires at least two codebases")

    environments = contract["environments"]
    checks = contract["required_checks"]
    branch_names: list[str] = []
    if not isinstance(environments, dict) or set(environments) != set(ROLES):
        errors.append("environments must contain exactly integration, staging, production")
        environments = {}
    if not isinstance(checks, dict) or set(checks) != set(ROLES):
        errors.append("required_checks must contain exactly integration, staging, production")
        checks = {}
    for role in ROLES:
        environment = environments.get(role, {})
        if not isinstance(environment, dict) or set(environment) != {
            "branch", "state", "deploy_enabled", "target",
        }:
            errors.append(
                f"environments.{role} must contain exactly branch, state, deploy_enabled, target"
            )
            continue
        branch = environment.get("branch")
        state = environment.get("state")
        deploy_enabled = environment.get("deploy_enabled")
        if validate_string(branch, f"environments.{role}.branch", errors):
            branch_names.append(branch)
        validate_string(environment.get("target"), f"environments.{role}.target", errors)
        if state not in {"observed", "planned"}:
            errors.append(f"environments.{role}.state must be observed or planned")
        if not isinstance(deploy_enabled, bool):
            errors.append(f"environments.{role}.deploy_enabled must be boolean")
        if state == "planned" and deploy_enabled is not False:
            errors.append(f"environments.{role}: planned branch requires deploy_enabled false")
        validate_role_checks(
            checks.get(role),
            f"required_checks.{role}",
            state == "observed",
            errors,
        )
    if duplicates(branch_names):
        integration_name = environments.get("integration", {}).get("branch")
        staging_name = environments.get("staging", {}).get("branch")
        production_name = environments.get("production", {}).get("branch")
        staging_is_integration = (
            integration_name == staging_name
            and isinstance(production_name, str)
            and production_name != integration_name
            and branch_names.count(integration_name) == 2
        )
        if not staging_is_integration:
            errors.append(
                "environment branch names must be unique except when staging is the integration branch"
            )

    integration_branch = environments.get("integration", {}).get("branch")
    for index, item in enumerate(repositories):
        if isinstance(item, dict) and item.get("integration_branch") != integration_branch:
            errors.append(
                f"repositories[{index}].integration_branch must match environments.integration.branch"
            )

    if contract["production_enabled"] is False:
        if environments.get("production", {}).get("deploy_enabled") is not False:
            errors.append("production_disabled requires production deployment disabled")
    else:
        if environments.get("production", {}).get("state") != "observed":
            errors.append("production deployment requires an observed production branch")
        if environments.get("production", {}).get("deploy_enabled") is not True:
            errors.append("production_enabled requires production deployment enabled")

    rollback = contract["rollback_refs"]
    placeholders = ("pending", "unconfirmed", "unknown", "tbd", "todo")
    if not isinstance(rollback, list) or not rollback:
        errors.append("rollback_refs must be a non-empty array")
    elif duplicates(rollback):
        errors.append("rollback_refs contains duplicates")
    elif any(
        not isinstance(ref, str) or not ref.strip() or ref.strip().lower().startswith(placeholders)
        for ref in rollback
    ):
        errors.append("active configuration requires concrete rollback_refs")

    provider_projects = contract.get("provider_projects", [])
    provider_pairs: list[tuple[str, str]] = []
    if not isinstance(provider_projects, list):
        errors.append("provider_projects must be an array")
        provider_projects = []
    for index, item in enumerate(provider_projects):
        expected = {"provider", "environment", "project_ref", "workdir"}
        if not isinstance(item, dict) or set(item) != expected:
            errors.append(
                f"provider_projects[{index}] must contain exactly provider, environment, project_ref, workdir"
            )
            continue
        for key in expected:
            validate_string(item.get(key), f"provider_projects[{index}].{key}", errors)
        provider = item.get("provider")
        environment = item.get("environment")
        project_ref = item.get("project_ref")
        workdir = item.get("workdir")
        provider_pairs.append((provider, environment))
        if provider != "supabase":
            errors.append(f"provider_projects[{index}].provider must equal supabase")
        if environment not in {"staging", "production"}:
            errors.append(
                f"provider_projects[{index}].environment must be staging or production"
            )
        if isinstance(project_ref, str) and not re.fullmatch(r"[a-z]{20}", project_ref):
            errors.append(f"provider_projects[{index}].project_ref is not a Supabase project ref")
        if isinstance(workdir, str):
            path = Path(workdir)
            if path.is_absolute() or ".." in path.parts:
                errors.append(
                    f"provider_projects[{index}].workdir must be repository-relative and contained"
                )
    if duplicates(provider_pairs):
        errors.append("provider_projects provider/environment pairs must be unique")

    if repo is not None and environments:
        observed_roles = [
            role for role in ROLES
            if environments.get(role, {}).get("state") == "observed"
        ]
        for index, item in enumerate(repositories):
            if not isinstance(item, dict):
                continue
            repository_root = repo / item["path"] if item["path"] != "." else repo
            if not repository_root.exists():
                errors.append(f"repositories[{index}]: path {item['path']!r} not found below repo")
                continue
            try:
                observed = git_branches(repository_root)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            for role in observed_roles:
                branch = environments[role]["branch"]
                if branch not in observed:
                    errors.append(
                        f"environments.{role}: observed branch {branch!r} not found in repository {item['id']!r}"
                    )

    scan_secrets(contract, "$", errors)
    return errors


def validate(contract: Any, repo: Path | None = None, require_active: bool = False) -> list[str]:
    if not isinstance(contract, dict):
        return ["contract root must be an object"]
    version = contract.get("schema_version")
    if version == 1:
        return validate_v1(contract, repo, require_active)
    if version == 2:
        return validate_v2(contract, repo, require_active)
    errors = ["schema_version must equal 1 or 2"]
    scan_secrets(contract, "$", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--repo", type=Path, help="Git repository used to verify observed branches")
    parser.add_argument("--require-active", action="store_true")
    args = parser.parse_args()
    try:
        contract = load_contract(args.contract)
        errors = validate(contract, args.repo, args.require_active)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        for error in errors: print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.contract}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
