#!/usr/bin/env python3
"""Read-only preflight/closeout check for repositories declared in delivery.yaml."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


class CheckoutError(RuntimeError):
    pass


@dataclass
class Result:
    repository: str
    path: str
    integration_branch: str
    branch: str | None
    head: str | None
    target_ref: str | None
    ahead: int | None
    behind: int | None
    dirty_entries: int | None
    verdict: str
    notes: list[str]


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )


def load_contract(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckoutError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CheckoutError("delivery.yaml debe contener un objeto JSON-compatible.")
    if value.get("configuration_status") != "active":
        raise CheckoutError("delivery.yaml debe estar activo para resolver checkouts.")
    return value


def declared_repositories(contract: dict) -> list[tuple[str, str, str]]:
    if contract.get("schema_version") == 2:
        repos = contract.get("repositories")
        if not isinstance(repos, list) or not repos:
            raise CheckoutError("El contrato v2 activo no declara repositories.")
        result = []
        for item in repos:
            if not isinstance(item, dict):
                raise CheckoutError("repositories contiene una entrada invalida.")
            result.append((item.get("id", ""), item.get("path", ""), item.get("integration_branch", "")))
        return result

    branches = contract.get("branches", {})
    integration = branches.get("integration", {}) if isinstance(branches, dict) else {}
    branch = integration.get("name", "") if isinstance(integration, dict) else ""
    return [(contract.get("project", "product"), ".", branch)]


def resolve_target_ref(repo: Path, integration: str) -> str | None:
    candidates: list[str] = []
    upstream = run(repo, "rev-parse", "--abbrev-ref", f"{integration}@{{upstream}}")
    if upstream.returncode == 0:
        candidates.append(upstream.stdout.strip())
    candidates.extend((f"origin/{integration}", integration))
    for candidate in candidates:
        if candidate and run(repo, "rev-parse", "--verify", "--quiet", candidate).returncode == 0:
            return candidate
    return None


def inspect(repo_id: str, repo: Path, integration: str, mode: str) -> Result:
    notes: list[str] = []
    if not repo.is_dir() or run(repo, "rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return Result(repo_id, str(repo), integration, None, None, None, None, None, None, "BLOCKED", ["no es un checkout Git"])
    if not integration:
        return Result(repo_id, str(repo), integration, None, None, None, None, None, None, "BLOCKED", ["integration_branch ausente"])

    branch_result = run(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    head_result = run(repo, "rev-parse", "HEAD")
    head = head_result.stdout.strip() if head_result.returncode == 0 else None
    target = resolve_target_ref(repo, integration)
    status = run(repo, "status", "--porcelain=v1")
    dirty = len([line for line in status.stdout.splitlines() if line]) if status.returncode == 0 else None

    ahead = behind = None
    if target and head:
        divergence = run(repo, "rev-list", "--left-right", "--count", f"{target}...HEAD")
        if divergence.returncode == 0:
            behind, ahead = (int(value) for value in divergence.stdout.split())

    verdict = "READY"
    if target is None:
        verdict = "BLOCKED"
        notes.append(f"no existe referencia local/remota para {integration}; ejecutar fetch y revisar contrato")
    elif mode == "closeout":
        if branch != integration:
            verdict = "BLOCKED"
            notes.append(f"checkout en {branch or 'detached'}, no en {integration}")
        if dirty:
            verdict = "BLOCKED"
            notes.append(f"{dirty} entradas sin integrar")
        if ahead or behind:
            verdict = "BLOCKED"
            notes.append(f"divergencia contra {target}: ahead={ahead}, behind={behind}")
    else:
        if dirty:
            verdict = "REVIEW"
            notes.append(f"{dirty} entradas locales: preservar o aislar antes de cambiar")
        if behind:
            verdict = "BLOCKED"
            notes.append(f"HEAD esta {behind} commit(s) detras de {target}")
        if branch != integration:
            ancestor = run(repo, "merge-base", "--is-ancestor", target, "HEAD") if target else None
            if ancestor is None or ancestor.returncode != 0:
                verdict = "BLOCKED"
                notes.append(f"{branch or 'detached'} no parte de {target}")
            else:
                notes.append(f"rama corta basada en {target}")

    if not notes:
        notes.append("checkout limpio y alineado")
    return Result(repo_id, str(repo), integration, branch, head, target, ahead, behind, dirty, verdict, notes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--repo", type=Path, help="Raiz del producto; por defecto, carpeta de delivery.yaml")
    parser.add_argument("--repository", action="append", dest="repositories", help="ID de repositorio v2 a inspeccionar; repetible")
    parser.add_argument("--mode", choices=("start", "closeout"), default="start")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract_path = args.contract.expanduser().resolve()
    root = (args.repo or contract_path.parent).expanduser().resolve()
    try:
        contract = load_contract(contract_path)
        declared = declared_repositories(contract)
    except CheckoutError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    selected = set(args.repositories or [])
    if selected:
        known = {repo_id for repo_id, _, _ in declared}
        unknown = selected - known
        if unknown:
            print(f"BLOCKED: repository desconocido: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        declared = [item for item in declared if item[0] in selected]

    results = [inspect(repo_id, (root / relpath).resolve(), branch, args.mode) for repo_id, relpath, branch in declared]
    if args.as_json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            short_head = result.head[:12] if result.head else "-"
            print(f"{result.verdict}\t{result.repository}\t{result.branch or '-'}\t{short_head}\t{'; '.join(result.notes)}")
    return 1 if any(result.verdict == "BLOCKED" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
