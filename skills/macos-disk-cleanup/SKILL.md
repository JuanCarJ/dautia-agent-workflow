---
name: macos-disk-cleanup
description: Diagnose macOS disk or performance pressure, organize files or reclaim authorized space. Audit first; deletion requires scope-specific authority.
---

# macOS Disk Cleanup

Reclaim space without treating the home directory as disposable. Measure first, preserve named exclusions exactly, delete only authorized targets, and prove the physical result.

## Classify the Request

Choose one mode before acting:

- `audit`: inspect and recommend; make no deletions.
- `targeted cleanup`: delete only the categories or exact paths the user named.
- `performance diagnosis`: inspect CPU, memory, disk pressure, active developer tools, and local virtualization before proposing cleanup.

Treat vague requests such as “what can I delete?” as `audit`. Treat direct requests such as “delete the DMGs in Downloads” as authorization for that exact category only.

Record every project, folder, or data class the user says not to touch. Keep the exclusion list visible during the whole operation. A later correction immediately expands the protected set.

## Audit Efficiently

Start read-only and avoid an expensive full-home scan. Check the physical volume first:

```bash
sw_vers
uptime
df -h / /System/Volumes/Data
tmutil listlocalsnapshots / 2>/dev/null || true
```

Inspect likely high-yield locations narrowly. Skip absent paths without treating that as failure:

```bash
du -sh \
  "$HOME/Downloads" \
  "$HOME/Library/Developer/XCTestDevices" \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Developer/Xcode/iOS DeviceSupport" \
  "$HOME/Library/Caches/Homebrew" \
  "$HOME/Library/Caches/ms-playwright" \
  "$HOME/.npm" \
  "$HOME/.gradle" \
  "$HOME/VirtualBox VMs" 2>/dev/null
```

Use targeted `du -xhd 1 <path> | sort -hr` only for a directory already shown to be large. Do not begin with recursive scans of all `~/Library` or the whole data volume.

Before deleting developer or virtualization artifacts, check active processes:

```bash
pgrep -fl 'Xcode|xcodebuild|Simulator|VirtualBox|VBox|qemu|colima|docker' || true
```

For `Downloads`, group candidates by type and size. Check installed applications before recommending their installers. Confirm duplicates by content hash, not by filename suffixes such as `(1)` or `(2)`. Isolate credentials such as `client_secret*.json`, keys, certificates, and `.env` files as sensitive review items.

## Build the Candidate List

Classify every candidate:

- `regenerable`: caches, DerivedData, old test devices, downloaded browser binaries, package caches.
- `review first`: DMGs, ISOs, archives, virtual machines, `node_modules`, build outputs, extracted duplicates.
- `protected`: source repositories, documents, credentials, photos, local databases, Docker volumes, or anything named as an exclusion.

Before mutation, present or internally verify this record for every target:

```text
path | logical size | category | regeneration cost | protected? | authorized?
```

Do not infer that a project dependency directory is disposable. A cross-repository `node_modules` or build-cache sweep needs a concrete inclusion rule and a rechecked exclusion list immediately before deletion.

## Execute Narrowly

Before the first deletion:

1. Capture `df -h /System/Volumes/Data`.
2. Reprint the protected paths and exact target list.
3. Verify relevant applications are stopped.
4. Prefer exact quoted paths over broad globs or name-based recursive sweeps.
5. Use Trash for reviewable user files when practical; permanently delete only when the user clearly requested actual deletion or Trash would not satisfy the request.

Never delete source code, documents, credentials, `.env` files, databases, Docker volumes, or persistent app data as part of a cache cleanup.

Stop immediately if a target resolves inside a protected path. If the user corrects scope after an action, stop the sweep, restore what can be deterministically restored, and verify the restored path before continuing.

Treat permission errors as partial failure. Do not claim a cache was removed merely because the command completed; remeasure the path.

## Handle Container Runtimes Separately

Inspect container provenance, Compose labels, restart policies, and builders before deciding they are residue. Colima is legacy residue and must never be installed, started, restarted, configured, or used. Read-only process/path detection is allowed; stop and report it if running, and delete its VM, data, or package only when the user explicitly authorizes those exact targets.

Do not remove images, builders, containers, volumes, or local databases unless the user authorized that exact class of deletion. After cleanup, verify only the exact target state requested; do not start a runtime to inspect or clean it.

## Verify the Result

After each meaningful deletion group:

- verify the exact target is absent or reduced;
- verify every protected path still exists as expected;
- rerun `df -h /System/Volumes/Data`;
- report physical free-space change, not only the sum of `du` sizes;
- note that APFS snapshots, sparse files, and clones can make logical and physical recovery differ;
- report residual permission errors or recreated caches explicitly.

Finish when the authorized targets are handled, exclusions are intact, no cleanup process is left running, and actual free space has been measured.

## Report

Close with:

- mode used: audit or targeted cleanup;
- largest measured consumers;
- exact categories or paths deleted;
- protected paths preserved;
- free space before and after;
- residual risks, permission failures, or items needing separate approval.

Never summarize a destructive sweep as simply “done.”
