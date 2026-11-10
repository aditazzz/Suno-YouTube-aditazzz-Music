#!/bin/bash
# One GPU job at a time on the Mac (Imaginative Prompting's rendering rule: two headless Chrome renders at once lose
# their WebGL contexts and blank frames). Usage:  tools/gpuq.sh [--first] <name> <command...>
# Waits for the lock, runs the command with its full output logged to logs/gpuq/<time>-<name>.log, then frees the lock.
# tools/gpuq.sh --status   shows who holds it and who is waiting.
# --first (or GPUQ_FIRST=1): a priority job (Nov 4, her OK: "the Short first"). While a live --first job is waiting,
#   ordinary jobs don't take the lock; the running job is never interrupted. Without --first nothing changes.
# --split: also share a Blender frame-range job with the render nodes (see tools/gpuq_split.sh).
# Within each class, jobs take the lock in arrival order (Nov 4, asked by the You Said You Needed Space producer).
# GPUQ_RUN=<dir> uses another lock folder (for testing the queue without touching the real one).
# Collision check (her rule, Nov 7: "an automatic check run every time a video frame is generated, catching objects cutting
#   through each other"): every Blender job is also dry-run on the CPU by tools/collide_gate.py (its own command, renders
#   become checks; sandboxed, nothing written), next to the render. A new visible penetration prints a FAIL banner and a
#   line in logs/collide/FAILS.txt. COLLIDE=strict also makes the job exit 3 after rendering, COLLIDE=block refuses to
#   render, COLLIDE=off skips the check. See .claude/skills/render-checks/SKILL.md "Collisions".
cd "$(dirname "$0")/.." || exit 1
RUN="${GPUQ_RUN:-_run}"
LOCK=$RUN/gpu.lock; WAIT=$RUN/gpu.waiting; mkdir -p "$RUN" logs/gpuq; touch "$WAIT"
if [ "$1" = "--status" ]; then
  if [ -d "$LOCK" ]; then echo "running: $(cat "$LOCK/owner" 2>/dev/null)"; else echo "free"; fi
  echo "waiting:"; cat "$WAIT"
  [ -s logs/collide/FAILS.txt ] && { echo "collision check FAILS (last 3; logs/collide/FAILS.txt):"; tail -3 logs/collide/FAILS.txt; }
  # render nodes (tools/gpuq_nodes.conf): short reachability check, never blocks
  if [ -f tools/gpuq_nodes.conf ]; then
    grep -v '^#' tools/gpuq_nodes.conf | while IFS='|' read -r nm tg ky rh wt en; do
      [ -n "$nm" ] && [ "$en" = 1 ] || continue; ky="${ky/#\~/$HOME}"
      if ssh -o BatchMode=yes -o ConnectTimeout=3 -i "$ky" "$tg" true 2>/dev/null; then echo "node $nm: online"; else echo "node $nm: offline (skipped)"; fi
    done
  fi
  exit 0
fi
FIRST="${GPUQ_FIRST:-0}"; [ "$1" = "--first" ] && { FIRST=1; shift; }
# --split: the job is a Blender frame-range render (Blender -b X.blend ... -s A -e B -a -- OUT) that tools/gpuq_split.sh
#   shares with the render nodes in tools/gpuq_nodes.conf (the Air); an unreachable node is skipped, its frames go to the M5.
SPLIT=0; [ "$1" = "--split" ] && { SPLIT=1; shift; }
[ "$1" = "--first" ] && { FIRST=1; shift; }
NAME="$1"; shift; [ -z "$NAME" ] || [ $# -eq 0 ] && { echo "usage: tools/gpuq.sh [--first] <name> <command...>"; exit 2; }
TAG=""; [ "$FIRST" = 1 ] && TAG=" first"
# collision check: a sandboxed CPU dry run of a Blender job (tools/collide_gate.py), started now and running next to the
# queue wait and the render, so it costs no GPU time; its verdict is printed when the job ends. COLLIDE=block runs it first.
CRC=0; CPID=""; COUT="logs/collide/.gate.$$.out"; mkdir -p logs/collide
PYC=.venv/bin/python; [ -x "$PYC" ] || PYC=python3
if [ "${COLLIDE:-warn}" = block ]; then
  "$PYC" tools/collide_gate.py "$NAME" "$@"; CRC=$?
  [ "$CRC" = 3 ] && { echo "[gpuq] $NAME NOT rendered: collision check failed and COLLIDE=block"; exit 3; }
elif [ "${COLLIDE:-warn}" != off ]; then
  "$PYC" tools/collide_gate.py "$NAME" "$@" > "$COUT" 2>&1 & CPID=$!
fi
echo "$NAME $(date '+%F %T') pid=$$$TAG" >> "$WAIT"

# A live --first waiter other than this job? (Old-format lines without pid= are never priority.)
priority_waiting() {
  local p
  for p in $(awk '/ first$/ { for (i=1;i<=NF;i++) if ($i ~ /^pid=/) print substr($i,5) }' "$WAIT" 2>/dev/null); do
    [ "$p" != "$$" ] && kill -0 "$p" 2>/dev/null && return 0
  done
  return 1
}
# Drop waiter lines whose process has died (new-format lines only).
prune_dead() {
  awk '{ keep=1; for (i=1;i<=NF;i++) if ($i ~ /^pid=/) { p=substr($i,5); if (system("kill -0 " p " 2>/dev/null")) keep=0 } if (keep) print }' \
    "$WAIT" > "$WAIT.tmp.$$" 2>/dev/null && mv "$WAIT.tmp.$$" "$WAIT"
}

# A live waiter of the same class (first / ordinary) that queued before this job? Then it goes first: arrival order.
# (Lines are appended on arrival, so file order is arrival order; old-format lines without pid= are skipped.)
earlier_waiting() {
  local mine="$1"
  awk -v me="$$" -v first="$mine" '
    { p=""; for (i=1;i<=NF;i++) if ($i ~ /^pid=/) p=substr($i,5); if (p=="") next
      if (p==me) exit
      isfirst = ($NF=="first") ? 1 : 0
      if (isfirst==first) print p }' "$WAIT" 2>/dev/null | while read -r p; do
    kill -0 "$p" 2>/dev/null && { echo yes; break; }
  done | grep -q yes
}

while :; do
  if [ "$FIRST" = 1 ] || ! priority_waiting; then
    earlier_waiting "$FIRST" || { mkdir "$LOCK" 2>/dev/null && break; }
  fi
  # A lock whose owner died is freed (pid check).
  P=$(awk '{print $2}' "$LOCK/owner" 2>/dev/null); [ -n "$P" ] && ! kill -0 "$P" 2>/dev/null && rm -rf "$LOCK"
  prune_dead
  sleep 5
done
echo "$NAME $$ $(date '+%F %T')$TAG" > "$LOCK/owner"
# Remove only this job's own line (old-format lines of the same name are left to their own process).
grep -v " pid=$$\( \|$\)" "$WAIT" > "$WAIT.tmp.$$"; mv "$WAIT.tmp.$$" "$WAIT"
LOG="logs/gpuq/$(date +%Y%m%d-%H%M%S)-$NAME.log"
trap 'rm -rf "$LOCK"' EXIT
echo "[gpuq] $NAME started $(date '+%T'), log: $LOG"
if [ "$SPLIT" = 1 ]; then tools/gpuq_split.sh "$@" > "$LOG" 2>&1; RC=$?; else "$@" > "$LOG" 2>&1; RC=$?; fi
if [ -n "$CPID" ]; then   # free the GPU first (and stop the EXIT trap, so it can't remove the next job's lock), then the verdict
  trap - EXIT; rm -rf "$LOCK"
  wait "$CPID"; CRC=$?; cat "$COUT" 2>/dev/null; rm -f "$COUT"
fi
[ "$CRC" = 3 ] && echo "[gpuq] $NAME: COLLISION CHECK FAILED for this render (objects cut through each other on screen); see logs/collide/FAILS.txt"
[ "$CRC" = 3 ] && [ "$COLLIDE" = strict ] && [ "$RC" = 0 ] && RC=3
echo "[gpuq] $NAME finished rc=$RC $(date '+%T')"; exit $RC
