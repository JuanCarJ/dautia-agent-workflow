#!/usr/bin/env bash
set -euo pipefail

root="${1:-$PWD}"

if [[ ! -d "$root" ]]; then
  echo "error: workspace does not exist: $root" >&2
  exit 2
fi

root="$(cd "$root" && pwd)"
echo "workspace=$root"

repos=()
while IFS= read -r git_dir; do
  repos+=("${git_dir%/.git}")
done < <(find "$root" -maxdepth 6 \
  \( -type d \( -name node_modules -o -name dist -o -name build -o -name .next -o -name .vercel \) -prune \) -o \
  \( -name .git \( -type d -o -type f \) -print -prune \) | sort)

echo "git_repositories=${#repos[@]}"

if [[ ${#repos[@]} -eq 0 ]]; then
  echo "warning=no Git repositories found"
else
  for repo in "${repos[@]}"; do
    branch="$(git -C "$repo" branch --show-current 2>/dev/null || true)"
    [[ -n "$branch" ]] || branch="DETACHED"
    status="$(git -C "$repo" status --porcelain=v1 --untracked-files=all)"
    modified=0
    deleted=0
    added=0
    untracked=0
    other=0
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      code="${line:0:2}"
      if [[ "$code" == "??" ]]; then
        ((untracked+=1))
      elif [[ "$code" == *M* ]]; then
        ((modified+=1))
      elif [[ "$code" == *D* ]]; then
        ((deleted+=1))
      elif [[ "$code" == *A* ]]; then
        ((added+=1))
      else
        ((other+=1))
      fi
    done <<< "$status"

    rel="${repo#$root}"
    [[ -n "$rel" ]] || rel="/"
    echo "repo=$rel branch=$branch modified=$modified deleted=$deleted added=$added untracked=$untracked other=$other"
    [[ -f "$repo/AGENTS.md" ]] && echo "  agents=present" || echo "  agents=missing"
    [[ -f "$repo/CLAUDE.md" ]] && echo "  claude=present" || echo "  claude=missing"
    [[ -f "$repo/docs/CURRENT.md" ]] && echo "  current=present" || echo "  current=missing"
    [[ -f "$repo/workspace.yaml" ]] && echo "  manifest=present" || echo "  manifest=missing"
    workflows=0
    if [[ -d "$repo/.github/workflows" ]]; then
      workflows="$(find "$repo/.github/workflows" -maxdepth 1 -type f | wc -l | tr -d ' ')"
    fi
    echo "  workflows=$workflows"
  done
fi

echo "documentation_directories"
while IFS= read -r docs_dir; do
  owner="$(git -C "$docs_dir" rev-parse --show-toplevel 2>/dev/null || true)"
  files="$(find "$docs_dir" -type f | wc -l | tr -d ' ')"
  rel="${docs_dir#$root}"
  [[ -n "$rel" ]] || rel="/docs"
  if [[ -n "$owner" ]]; then
    echo "  docs=$rel files=$files versioned_by=$owner"
  else
    echo "  docs=$rel files=$files versioned_by=NONE warning=normative-risk"
  fi
done < <(find "$root" -maxdepth 4 \
  \( -type d \( -name .git -o -name node_modules -o -name dist -o -name build -o -name .next -o -name .vercel \) -prune \) -o \
  \( -type d -name docs -prune -print \) | sort)

echo "agent_contracts"
find "$root" -maxdepth 6 \
  \( -type d \( -name .git -o -name node_modules -o -name dist -o -name build -o -name .next -o -name .vercel \) -prune \) -o \
  \( -type f \( -name AGENTS.md -o -name CLAUDE.md \) -print \) | sort | sed "s#^$root#  #"
