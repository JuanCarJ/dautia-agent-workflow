#!/usr/bin/env python3
"""Run Supabase CLI with project identity and non-interactive local credentials."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import platform
import pty
import re
import select
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


KEYCHAIN_SERVICE = "com.dautia.supabase.db-password"
ACCESS_TOKEN_FILE = Path.home() / ".supabase" / "access-token"
DEFAULT_CREDENTIAL_FILE = Path.home() / ".config" / "dautia" / "supabase-db-credentials.json"
PROJECT_REF = re.compile(r"^[a-z]{20}$")
EXCLUDED_DIRS = {".git", ".worktrees", "node_modules", "build", "dist", ".next", "DerivedData"}


class SetupError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    root: Path
    environment: str
    project_ref: str
    workdir: Path
    source: str


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"No se pudo leer {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SetupError(f"{path} no contiene un objeto JSON-compatible YAML.")
    return value


def find_root(start: Path) -> Path:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "delivery.yaml").is_file():
            return candidate
    raise SetupError("No se encontro delivery.yaml desde el directorio indicado.")


def read_ref(path: Path) -> str | None:
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    if not PROJECT_REF.fullmatch(value):
        raise SetupError(f"Project ref invalido en {path}.")
    return value


def linked_ref_files(root: Path) -> list[Path]:
    matches: list[Path] = []
    for directory, names, files in os.walk(root):
        names[:] = [name for name in names if name not in EXCLUDED_DIRS]
        path = Path(directory)
        if path.name == ".temp" and "project-ref" in files and path.parent.name == "supabase":
            matches.append(path / "project-ref")
    return sorted(matches)


def current_linked_ref(workdir: Path) -> str | None:
    return read_ref(workdir / "supabase" / ".temp" / "project-ref")


def resolve_target(start: Path, environment: str, require_link_match: bool = True) -> Target:
    root = find_root(start)
    contract = load_json(root / "delivery.yaml")
    entries = contract.get("provider_projects", [])
    selected = [
        entry for entry in entries
        if isinstance(entry, dict)
        and entry.get("provider") == "supabase"
        and entry.get("environment") == environment
    ]
    if len(selected) > 1:
        raise SetupError(f"delivery.yaml repite Supabase para {environment}.")

    if selected:
        entry = selected[0]
        project_ref = entry.get("project_ref", "")
        if not PROJECT_REF.fullmatch(project_ref):
            raise SetupError("delivery.yaml contiene un project_ref Supabase invalido.")
        workdir = (root / entry.get("workdir", "")).resolve()
        try:
            workdir.relative_to(root)
        except ValueError as exc:
            raise SetupError("El workdir Supabase debe permanecer dentro del producto.") from exc
        if not workdir.is_dir():
            raise SetupError(f"No existe el workdir Supabase declarado: {workdir}")
        source = "delivery.yaml"
    else:
        control = contract.get("database_change_control", {})
        targets = control.get("targets", {}) if isinstance(control, dict) else {}
        entry = targets.get(environment) if isinstance(targets, dict) else None
        if isinstance(entry, dict):
            project_ref = entry.get("project_ref", "")
            if not PROJECT_REF.fullmatch(project_ref):
                raise SetupError("database_change_control contiene un project_ref Supabase invalido.")
            workdir = (root / entry.get("workdir", ".")).resolve()
            try:
                workdir.relative_to(root)
            except ValueError as exc:
                raise SetupError("El workdir Supabase debe permanecer dentro del producto.") from exc
            if not workdir.is_dir():
                raise SetupError(f"No existe el workdir Supabase declarado: {workdir}")
            source = "database_change_control"
        else:
            refs = linked_ref_files(root)
            if not refs:
                raise SetupError(
                    "delivery.yaml no declara un target Supabase y no existe un unico link legado."
                )
            if len(refs) > 1:
                raise SetupError(
                    "Hay varios links Supabase legados; declara los targets en delivery.yaml."
                )
            project_ref = read_ref(refs[0])
            assert project_ref
            workdir = refs[0].parent.parent.parent
            source = "legacy-link"

    linked = current_linked_ref(workdir)
    if require_link_match and linked and linked != project_ref:
        raise SetupError(
            f"Identidad contradictoria: target={project_ref}, linked={linked}. "
            f"Ejecuta `dautia-supabase activate --environment {environment}`."
        )
    return Target(root, environment, project_ref, workdir, source)


def security_bin() -> str:
    configured = os.environ.get("DAUTIA_SECURITY_BIN", "").strip()
    if configured:
        return configured
    return shutil.which("security") or "/usr/bin/security"


def supports_keychain() -> bool:
    return platform.system() == "Darwin" and Path(security_bin()).is_file()


def credential_file() -> Path:
    configured = os.environ.get("DAUTIA_SUPABASE_CREDENTIAL_FILE", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_CREDENTIAL_FILE


def credential_registry() -> dict[str, str]:
    path = credential_file()
    try:
        stat = path.stat()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise SetupError(f"No se pudo inspeccionar {path}.") from exc
    if not path.is_file() or path.is_symlink():
        raise SetupError(f"{path} debe ser un archivo regular, no un enlace.")
    if stat.st_mode & 0o077:
        raise SetupError(f"{path} debe tener permisos 0600 antes de usarse.")
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"No se pudo leer el registro protegido {path}.") from exc
    if not isinstance(values, dict) or any(
        not PROJECT_REF.fullmatch(key) or not isinstance(value, str) or not value
        for key, value in values.items()
    ):
        raise SetupError(f"{path} contiene credenciales invalidas.")
    return values


def credential_registry_get(project_ref: str) -> str | None:
    return credential_registry().get(project_ref)


def credential_registry_set(project_ref: str, password: str) -> None:
    if not PROJECT_REF.fullmatch(project_ref) or not password:
        raise SetupError("No se puede guardar una credencial local invalida.")
    path = credential_file()
    values = credential_registry()
    values[project_ref] = password
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.parent.chmod(0o700)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(values, stream, sort_keys=True)
                stream.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        os.replace(temporary, path)
        path.chmod(0o600)
    except OSError as exc:
        raise SetupError(f"No se pudo actualizar el registro protegido {path}.") from exc


def keychain_get(project_ref: str) -> str | None:
    if not supports_keychain():
        return None
    try:
        result = subprocess.run(
            [security_bin(), "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", project_ref, "-w"],
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode:
        return None
    value = result.stdout.rstrip("\n")
    return value or None


def keychain_set(project_ref: str, password: str) -> None:
    if not supports_keychain():
        raise SetupError("Keychain solo esta disponible en macOS.")
    if not password:
        raise SetupError("La contrasena no puede estar vacia.")
    command = [
        security_bin(), "add-generic-password", "-U", "-s", KEYCHAIN_SERVICE,
        "-a", project_ref, "-l", f"DautIA Supabase DB {project_ref}",
        "-T", security_bin(), "-w",
    ]
    pid, master = pty.fork()
    if pid == 0:
        os.execv(command[0], command)
    buffer = b""
    sent = 0
    deadline = time.monotonic() + 15
    returncode: int | None = None
    try:
        while time.monotonic() < deadline:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                returncode = os.waitstatus_to_exitcode(status)
                break
            readable, _, _ = select.select([master], [], [], 0.25)
            if not readable:
                continue
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk.lower()
            if sent == 0 and b"password data for" in buffer:
                os.write(master, password.encode("utf-8") + b"\n")
                sent = 1
                buffer = b""
            elif sent == 1 and b"retype password" in buffer:
                os.write(master, password.encode("utf-8") + b"\n")
                sent = 2
                buffer = b""
        if returncode is None:
            os.kill(pid, 15)
            _, status = os.waitpid(pid, 0)
            returncode = os.waitstatus_to_exitcode(status)
    finally:
        os.close(master)
    if returncode or sent != 2:
        raise SetupError("No se pudo guardar la credencial en el Llavero de macOS.")


def access_token() -> str | None:
    """Resolve the account token without asking the Supabase CLI Keychain."""
    configured = os.environ.get("SUPABASE_ACCESS_TOKEN", "").strip()
    if configured:
        return configured
    try:
        mode = ACCESS_TOKEN_FILE.stat().st_mode
        if mode & 0o077:
            raise SetupError(
                f"{ACCESS_TOKEN_FILE} debe tener permisos 0600 antes de usarse."
            )
        value = ACCESS_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as exc:
        raise SetupError(f"No se pudo leer {ACCESS_TOKEN_FILE}.") from exc
    return value or None


def cli_environment() -> dict[str, str]:
    child_env = os.environ.copy()
    token = access_token()
    if token:
        child_env["SUPABASE_ACCESS_TOKEN"] = token
    return child_env


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
            value = re.sub(r"\\([\\\"$])", r"\1", value).replace("\\n", "\n")
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        values[key] = value
    return values


def env_matches_ref(values: dict[str, str], project_ref: str) -> bool:
    candidates = {
        values.get("SUPABASE_PROJECT_ID", ""),
        values.get("SUPABASE_PROJECT_REF", ""),
    }
    for key in ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"):
        match = re.search(r"https://([a-z]{20})\.supabase\.co", values.get(key, ""))
        if match:
            candidates.add(match.group(1))
    return project_ref in candidates


def env_files(root: Path) -> Iterable[Path]:
    for directory, names, files in os.walk(root):
        names[:] = [name for name in names if name not in EXCLUDED_DIRS]
        for name in files:
            if name in {".env", ".env.local", ".env.staging.local", ".env.production.local"}:
                yield Path(directory) / name


def existing_env_password(target: Target) -> tuple[str | None, Path | None]:
    found: list[tuple[str, Path]] = []
    current = dict(os.environ)
    if env_matches_ref(current, target.project_ref) and current.get("SUPABASE_DB_PASSWORD"):
        found.append((current["SUPABASE_DB_PASSWORD"], Path("<process-env>")))
    for path in env_files(target.root):
        try:
            values = parse_dotenv(path)
        except (OSError, UnicodeError):
            continue
        password = values.get("SUPABASE_DB_PASSWORD", "")
        if password and env_matches_ref(values, target.project_ref):
            found.append((password, path))
    distinct = {password for password, _ in found}
    if len(distinct) > 1:
        raise SetupError(
            "Existen contrasenas distintas para el mismo project_ref; no se importo ninguna."
        )
    return found[0] if found else (None, None)


def supabase_bin() -> str:
    configured = os.environ.get("SUPABASE_CLI_BIN", "").strip()
    if configured:
        return configured
    discovered = shutil.which("supabase")
    if discovered:
        return discovered
    raise SetupError(
        "No se encontro Supabase CLI en PATH. Instalalo una vez en este host."
    )


def cli_prefix(target: Target | None = None) -> list[str]:
    args = [supabase_bin(), "--agent", "no", "--profile", "supabase"]
    if target:
        args.extend(["--workdir", str(target.workdir)])
    return args


def verify_cli_account(project_ref: str) -> None:
    child_env = cli_environment()
    try:
        result = subprocess.run(
            [*cli_prefix(), "projects", "list", "-o", "json"],
            stdin=subprocess.DEVNULL,
            env=child_env,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired as exc:
        raise SetupError(
            "Supabase CLI no respondio al verificar la cuenta; no se abrira un prompt."
        ) from exc
    if result.returncode:
        raise SetupError("Supabase CLI no esta autenticado. Ejecuta una vez: supabase login")
    try:
        projects = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SetupError("Supabase CLI devolvio una respuesta de cuenta invalida.") from exc
    refs = {item.get("id") or item.get("ref") for item in projects if isinstance(item, dict)}
    if project_ref not in refs:
        raise SetupError(f"La cuenta CLI no tiene acceso al proyecto {project_ref}.")


def settings_url(project_ref: str) -> str:
    return f"https://supabase.com/dashboard/project/{project_ref}/settings/database"


def require_password(project_ref: str, environment: str | None = None) -> str:
    cached = credential_registry_get(project_ref)
    if cached:
        return cached
    password = keychain_get(project_ref)
    if password:
        credential_registry_set(project_ref, password)
        return password
    environment_arg = f" --environment {environment}" if environment else ""
    raise SetupError(
        "No hay contrasena DB en el registro protegido de este host. Ejecuta "
        f"`dautia-supabase bootstrap{environment_arg}`; si no la conoces, "
        f"restablecela en {settings_url(project_ref)}."
    )


def command_needs_password(command: list[str]) -> bool:
    if not command:
        return False
    if command[:2] == ["migration", "new"]:
        return False
    return command[0] in {"db", "link", "migration", "inspect", "seed"}


def ensure_target_link(target: Target, child_env: dict[str, str]) -> None:
    """Materialize a missing local link without allowing an interactive prompt.

    Supabase keeps the linked project ref in an ignored `.temp` directory, so a
    fresh Git worktree never inherits it. The stable identity remains
    `delivery.yaml`; an existing contradictory link must still fail closed.
    """
    linked = current_linked_ref(target.workdir)
    if linked == target.project_ref:
        return
    if linked is not None:
        raise SetupError(
            f"Identidad contradictoria: target={target.project_ref}, linked={linked}. "
            f"Ejecuta `dautia-supabase activate --environment {target.environment}`."
        )
    result = subprocess.run(
        [
            *cli_prefix(target),
            "link",
            "--project-ref",
            target.project_ref,
            "--yes",
        ],
        cwd=target.root,
        env=child_env,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode:
        raise SetupError(
            "No se pudo autoenlazar el checkout al target declarado sin interaccion. "
            f"Ejecuta `dautia-supabase doctor --environment {target.environment}`."
        )
    if current_linked_ref(target.workdir) != target.project_ref:
        raise SetupError(
            "Supabase CLI termino sin materializar el project_ref declarado en el checkout."
        )


def cmd_bootstrap(args: argparse.Namespace) -> int:
    target = resolve_target(Path(args.root), args.environment, require_link_match=False)
    verify_cli_account(target.project_ref)
    if credential_registry_get(target.project_ref):
        print(f"OK: {target.project_ref} ya tiene credencial DB no interactiva.")
        return 0
    existing_keychain = keychain_get(target.project_ref)
    if existing_keychain:
        credential_registry_set(target.project_ref, existing_keychain)
        print(f"OK: credencial existente importada al registro local protegido para {target.project_ref}.")
        return 0
    password, source = existing_env_password(target)
    if password:
        if supports_keychain():
            keychain_set(target.project_ref, password)
        credential_registry_set(target.project_ref, password)
        print(f"OK: credencial importada desde {source}; el valor no se mostro.")
        return 0
    print(f"FALTA_CREDENCIAL: {target.project_ref}")
    print(f"Si no la conoces, restablecela en: {settings_url(target.project_ref)}")
    print(f"Luego ejecuta: dautia-supabase credential set --project-ref {target.project_ref}")
    return 2


def cmd_doctor(args: argparse.Namespace) -> int:
    target = resolve_target(Path(args.root), args.environment, require_link_match=False)
    try:
        verify_cli_account(target.project_ref)
        cli = "ok"
    except SetupError:
        cli = "missing"
    credential = "present" if credential_registry_get(target.project_ref) else "missing"
    linked = current_linked_ref(target.workdir)
    link_status = "ok" if linked == target.project_ref else "missing" if linked is None else "mismatch"
    print(f"root={target.root}")
    print(f"environment={target.environment}")
    print(f"project_ref={target.project_ref}")
    print(f"workdir={target.workdir}")
    print(f"identity_source={target.source}")
    print(f"linked_project_ref={linked or 'missing'}")
    print(f"link_status={link_status}")
    print(f"cli_account={cli}")
    print(f"db_credential={credential}")
    return 0 if cli == "ok" and credential == "present" and link_status == "ok" else 2


def cmd_activate(args: argparse.Namespace) -> int:
    target = resolve_target(Path(args.root), args.environment, require_link_match=False)
    child_env = cli_environment()
    child_env["SUPABASE_DB_PASSWORD"] = require_password(
        target.project_ref, target.environment
    )
    if current_linked_ref(target.workdir) == target.project_ref:
        print(f"OK: environment={target.environment} project_ref={target.project_ref}")
        return 0
    try:
        result = subprocess.run(
            [
                *cli_prefix(target),
                "link",
                "--project-ref",
                target.project_ref,
                "--yes",
            ],
            cwd=target.root,
            env=child_env,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise SetupError(
            "Supabase CLI no respondio al enlazar; se cerro sin pedir credenciales."
        ) from exc
    if result.returncode:
        raise SetupError(
            "No se pudo enlazar el target declarado sin interaccion. "
            "La contrasena no se volvera a solicitar."
        )
    if current_linked_ref(target.workdir) != target.project_ref:
        raise SetupError("Supabase CLI termino sin dejar enlazado el project_ref esperado.")
    print(f"OK: environment={target.environment} project_ref={target.project_ref}")
    return 0


def cmd_credential_set(args: argparse.Namespace) -> int:
    if not PROJECT_REF.fullmatch(args.project_ref):
        raise SetupError("project_ref invalido.")
    password = getpass.getpass("Contrasena PostgreSQL de Supabase: ")
    confirmation = getpass.getpass("Repetir contrasena: ")
    if password != confirmation:
        raise SetupError("Las contrasenas no coinciden.")
    if supports_keychain():
        keychain_set(args.project_ref, password)
    credential_registry_set(args.project_ref, password)
    print(f"OK: credencial guardada para acceso no interactivo a {args.project_ref}.")
    return 0


def cmd_credential_status(args: argparse.Namespace) -> int:
    if not PROJECT_REF.fullmatch(args.project_ref):
        raise SetupError("project_ref invalido.")
    present = credential_registry_get(args.project_ref) is not None
    print("present" if present else "missing")
    return 0 if present else 2


def cmd_run(args: argparse.Namespace) -> int:
    target = resolve_target(Path(args.root), args.environment)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SetupError("Falta el comando Supabase despues de --.")
    if command[0] == "link":
        raise SetupError(
            "No uses `supabase link` dentro de un proyecto administrado. "
            f"Usa `dautia-supabase activate --environment {target.environment}`."
        )
    child_env = cli_environment()
    if command_needs_password(command):
        child_env["SUPABASE_DB_PASSWORD"] = require_password(
            target.project_ref, target.environment
        )
        ensure_target_link(target, child_env)
    result = subprocess.run(
        [*cli_prefix(target), *command],
        cwd=target.root,
        env=child_env,
        check=False,
    )
    return result.returncode


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="action", required=True)
    for name, handler in (
        ("bootstrap", cmd_bootstrap),
        ("doctor", cmd_doctor),
        ("activate", cmd_activate),
    ):
        item = sub.add_parser(name)
        item.add_argument("--root", default=".")
        item.add_argument("--environment", choices=("staging", "production"), default="staging")
        item.set_defaults(handler=handler)

    credential = sub.add_parser("credential")
    credential_sub = credential.add_subparsers(dest="credential_action", required=True)
    set_item = credential_sub.add_parser("set")
    set_item.add_argument("--project-ref", required=True)
    set_item.set_defaults(handler=cmd_credential_set)
    status_item = credential_sub.add_parser("status")
    status_item.add_argument("--project-ref", required=True)
    status_item.set_defaults(handler=cmd_credential_status)

    run = sub.add_parser("run")
    run.add_argument("--root", default=".")
    run.add_argument("--environment", choices=("staging", "production"), default="staging")
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(handler=cmd_run)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except SetupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
