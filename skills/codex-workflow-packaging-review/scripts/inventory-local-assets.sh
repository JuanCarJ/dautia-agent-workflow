#!/usr/bin/env bash
set -euo pipefail

codex_home="${CODEX_HOME:-$HOME/.codex}"

printf 'Personal skills\n'
if [[ -d "$codex_home/skills" ]]; then
  find "$codex_home/skills" -mindepth 2 -maxdepth 2 -name SKILL.md -print \
    | sed 's#/SKILL.md$##' \
    | sort
fi

printf '\nCustom agents\n'
if [[ -d "$codex_home/agents" ]]; then
  find "$codex_home/agents" -maxdepth 1 -type f -name '*.toml' -print | sort
fi

printf '\nLocal automations\n'
if [[ -d "$codex_home/automations" ]]; then
  find "$codex_home/automations" -mindepth 2 -maxdepth 2 -name automation.toml -print | sort
fi
