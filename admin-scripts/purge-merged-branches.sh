#!/usr/bin/env bash
set -euo pipefail

# Purge (delete) branches fully merged into the base branch.
# Defaults:
#   Base branch: origin/main (override with BASE env var or --base <branch>)
#   Protected branches: main master develop dev release staging production
# Features:
#   * Dry run by default when -n/--dry-run is used
#   * Local branch deletion (default)
#   * Optional remote branch deletion (-r / --remote)
#   * Add extra protected branches with repeated --protect <name>
#   * Force delete unmerged local branches with -f / --force (avoid unless needed)
#   * Verbose mode -v for extra logging
#
# Usage examples:
#   bash admin-scripts/purge-merged-branches.sh --dry-run
#   bash admin-scripts/purge-merged-branches.sh -r   # also delete remote merged branches
#   bash admin-scripts/purge-merged-branches.sh --protect experimental --dry-run
#   BASE=origin/develop bash admin-scripts/purge-merged-branches.sh -r

BASE="${BASE:-origin/main}"
DRY_RUN=false
DO_REMOTE=false
FORCE=false
VERBOSE=false
PROTECTED=(main master develop dev release staging production)

die() { echo "Error: $*" >&2; exit 1; }
log() { echo "[purge] $*"; }
vlog() { $VERBOSE && echo "[purge][debug] $*" || true; }

usage() {
  grep '^# ' "$0" | sed 's/^# //'
  echo
  echo "Options:"
  echo "  --base <branch>        Base branch to compare (default: $BASE)"
  echo "  -n, --dry-run          Show what would be deleted without deleting"
  echo "  -r, --remote           Also delete merged remote branches (origin/*)"
  echo "  -f, --force            Force delete local branches (-D instead of -d)"
  echo "      --protect <name>   Add extra protected branch (repeatable)"
  echo "  -v, --verbose          Verbose debug logging"
  echo "  -h, --help             Show this help"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2;;
    -n|--dry-run) DRY_RUN=true; shift;;
    -r|--remote) DO_REMOTE=true; shift;;
    -f|--force) FORCE=true; shift;;
    --protect) PROTECTED+=("$2"); shift 2;;
    -v|--verbose) VERBOSE=true; shift;;
    -h|--help) usage; exit 0;;
    *) die "Unknown argument: $1";;
  esac
done

command -v git >/dev/null 2>&1 || die "git not found in PATH"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repository"

# Ensure we have the latest refs
log "Fetching updates (pruning deleted remotes)..."
git fetch --prune --quiet || die "git fetch failed"

git rev-parse --verify "$BASE" >/dev/null 2>&1 || die "Base ref '$BASE' not found"
BASE_SHORT="${BASE#origin/}"

log "Base branch: $BASE"
log "Protected branches: ${PROTECTED[*]}"
$DRY_RUN && log "(dry run mode)"

is_protected() {
  local b="$1"
  for p in "${PROTECTED[@]}"; do
    [[ "$b" == "$p" ]] && return 0
  done
  return 1
}

delete_local_branch() {
  local b="$1"
  if $DRY_RUN; then
    echo "Would delete local branch: $b"
  else
    if $FORCE; then
      git branch -D "$b"
    else
      git branch -d "$b"
    fi
  fi
}

delete_remote_branch() {
  local b="$1"
  if $DRY_RUN; then
    echo "Would delete remote branch: origin/$b"
  else
    git push origin --delete "$b"
  fi
}

log "Analyzing local merged branches..."

# List local branches merged into BASE
mapfile -t LOCAL_MERGED < <(git branch --format '%(refname:short)' --merged "$BASE")
mapfile -t ALL_LOCAL < <(git branch --format '%(refname:short)')
CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || true)

LOCAL_COUNT=0
LOCAL_KEPT=()

in_array() { # needle list...
  local n="$1"; shift
  local x
  for x in "$@"; do [[ "$x" == "$n" ]] && return 0; done
  return 1
}

for b in "${LOCAL_MERGED[@]}"; do
  [[ -z "$b" ]] && continue
  if [[ "$b" == "$BASE_SHORT" ]]; then
    LOCAL_KEPT+=("$b (base)")
    continue
  fi
  if is_protected "$b"; then
    vlog "skip protected local $b"
    LOCAL_KEPT+=("$b (protected, merged)")
    continue
  fi
  delete_local_branch "$b" && LOCAL_COUNT=$((LOCAL_COUNT+1)) || true
done

# Add unmerged local branches (kept) with reasons
for b in "${ALL_LOCAL[@]}"; do
  [[ -z "$b" ]] && continue
  in_array "$b" "${LOCAL_MERGED[@]}" && continue # already handled
  if [[ "$b" == "$BASE_SHORT" ]]; then
    in_array "$b" "${LOCAL_KEPT[@]}" || LOCAL_KEPT+=("$b (base)")
    continue
  fi
  if is_protected "$b"; then
    LOCAL_KEPT+=("$b (protected, not merged)")
    continue
  fi
  if [[ "$b" == "$CURRENT_BRANCH" ]]; then
    LOCAL_KEPT+=("$b (current, not merged)")
  else
    LOCAL_KEPT+=("$b (not merged)")
  fi
done

log "Local branches considered (merged set): ${#LOCAL_MERGED[@]} ; deleted (or would delete): $LOCAL_COUNT"
if $DRY_RUN; then
  echo "--- Local branches NOT deleted ---"
  if ((${#LOCAL_KEPT[@]}==0)); then
    echo "(none)"
  else
    printf '%s\n' "${LOCAL_KEPT[@]}" | sort
  fi
fi

if $DO_REMOTE; then
  log "Analyzing remote merged branches..."
  # Enumerate remote branches (excluding HEAD symbolic ref)
  mapfile -t REMOTE_BRANCHES < <(git for-each-ref --format '%(refname:short)' refs/remotes/origin | sed 's#^origin/##' | grep -v '^HEAD$')
  REMOTE_COUNT=0
  REMOTE_KEPT=()
  for b in "${REMOTE_BRANCHES[@]}"; do
    if [[ "$b" == "$BASE_SHORT" ]]; then
      REMOTE_KEPT+=("$b (base)")
      continue
    fi
    if is_protected "$b"; then
      vlog "skip protected remote $b"
      REMOTE_KEPT+=("$b (protected)")
      continue
    fi
    # Check if origin/b is merged into BASE
    if git merge-base --is-ancestor "origin/$b" "$BASE"; then
      delete_remote_branch "$b" && REMOTE_COUNT=$((REMOTE_COUNT+1)) || true
    else
      vlog "remote $b not fully merged into $BASE"
      REMOTE_KEPT+=("$b (not merged)")
    fi
  done
  log "Remote branches considered: ${#REMOTE_BRANCHES[@]} ; deleted (or would delete): $REMOTE_COUNT"
  if $DRY_RUN; then
    echo "--- Remote branches NOT deleted ---"
    if ((${#REMOTE_KEPT[@]}==0)); then
      echo "(none)"
    else
      printf '%s\n' "${REMOTE_KEPT[@]}" | sort
    fi
  fi
fi

log "Done."
