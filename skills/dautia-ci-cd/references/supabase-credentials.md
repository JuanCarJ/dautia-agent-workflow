# Supabase credentials

Use three independent authentication paths:

- Supabase account CLI: the global session created by `supabase login`; the
  wrapper injects the official `~/.supabase/access-token` fallback when present
  and requires that file to remain `0600`;
- Supabase MCP: the installed official connector and its OAuth session;
- remote Postgres: one database password per `project_ref`; onboarding imports
  it into `~/.config/dautia/supabase-db-credentials.json` (`0600`) for
  non-interactive runs. macOS may retain the same value in Keychain; WSL uses
  the protected registry directly.

Application URLs, publishable keys, and server-only keys remain in ignored local
environment files or the deployment provider. They do not authenticate the CLI
or MCP. `SUPABASE_DB_PASSWORD` may exist briefly in the ignored environment file
during onboarding, but after import it belongs only in the global credential
stores and not in any project.

## Contract

An active `delivery.yaml` can declare:

```json
"provider_projects": [
  {
    "provider": "supabase",
    "environment": "staging",
    "project_ref": "abcdefghijklmnopqrst",
    "workdir": "."
  }
]
```

The project ref is an identifier, not a secret. `workdir` is the directory that
contains `supabase/`, matching the CLI `--workdir` contract. Keep one entry per
provider and environment. Production, when provisioned, uses a distinct entry
and credential. A legacy `database_change_control.targets.<environment>` map is
also resolved while projects migrate to the standard contract.

## One-time bootstrap

From the product root:

```bash
dautia-supabase bootstrap --environment staging
dautia-supabase doctor --environment staging
```

Bootstrap verifies the global CLI session, resolves the target from
`delivery.yaml`, and imports an existing macOS Keychain item or a matching
password from an ignored local env file into the protected non-interactive
registry. On WSL, `credential set` receives it through hidden terminal input
and writes only that registry. It never prints the value. Keychain is not
consulted again during normal commands. If no matching password is
available, it returns the exact Supabase project settings URL. Reset the database
password there only after identifying consumers that use the old connection,
then store the new value through hidden terminal input:

```bash
dautia-supabase credential set --project-ref <project-ref>
```

Do not provide the password in chat or as a command-line argument.

Do not move the account access token into a project `.env`. The wrapper prefers
the official `~/.supabase/access-token` fallback on every host and passes it
only to the child CLI as `SUPABASE_ACCESS_TOKEN`; it never prints it. This also
avoids macOS Keychain ACL prompts after a CLI binary update.

For the one-time env path, use the environment-specific ignored file and include
an identifier that lets the wrapper reject a password for the wrong project:

```dotenv
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_DB_PASSWORD=<database-password>
```

Run bootstrap, confirm `db_credential=present`, and immediately remove only the
`SUPABASE_DB_PASSWORD` line. Application keys stay where the application needs
them.

## More than one Supabase project

Bootstrap each independent ref once. Linking is a local, explicit operation:

```bash
dautia-supabase bootstrap --environment staging
dautia-supabase bootstrap --environment production
dautia-supabase activate --environment staging
dautia-supabase doctor --environment staging
```

Before a separately authorized production operation, activate production
explicitly and run doctor for production. Restore staging afterward when it is
the checkout's normal test target. `run` never switches environments silently.

## Normal CLI use

Run linked database commands through:

```bash
dautia-supabase run --environment staging -- db push --dry-run
```

The wrapper verifies the declared and locally linked project refs, retrieves the
password from the protected global registry, injects it only into the child environment, and uses the
authenticated global CLI session without asking the CLI Keychain. Missing or contradictory identity stops the
command. This does not grant authority to link, migrate, seed, reset, deploy, or
touch production; the normal delivery and release rules still apply.

`run` materializes a missing local link automatically from the explicit
environment in `delivery.yaml`. This is necessary for fresh Git worktrees
because `supabase/.temp/project-ref` is intentionally ignored. Auto-link uses
the protected registry credential, `--yes`, and closed stdin; it never asks for a password.
An existing contradictory link still fails closed and must be changed with
`dautia-supabase activate --environment <target>`. Direct `supabase link` is
blocked inside managed projects so it cannot open an interactive wizard.
The normal `run` and `activate` paths do not enumerate every project in the
Supabase account. `activate` is idempotent, closes stdin and has a bounded
timeout. The account-level check remains in `bootstrap` and `doctor`; it also
uses closed stdin and a timeout, while the requested CLI command reports an
expired or unauthorized session directly.

`doctor` proves target identity, account access, local link, and protected
registry presence; before the first `run` in a fresh worktree it may report the link as
missing. It does not authenticate the stored password against Postgres. When a
real credential smoke is justified, use a read-only linked inspection:

```bash
dautia-supabase run --environment staging -- inspect db db-stats --linked
```

For a project wrapper such as Templo Rojo, use its equivalent
`npm run supabase -- inspect db db-stats --linked`. Production requires explicit
authority even for this smoke. Never extract the password into a command-line
argument or bypass the wrapper with direct `psql`; the wrapper injects it only
into the child process. After a temporary multi-environment verification,
restore the checkout's normal staging link and confirm it with `doctor`.

Use the official Supabase connector for MCP inspection. Do not add a second
project-scoped MCP server to global Codex configuration; it duplicates OAuth and
becomes stale when work moves to another project.
