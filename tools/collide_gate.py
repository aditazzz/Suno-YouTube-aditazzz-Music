#!/usr/bin/env python3
"""collide_gate.py: the collision check for one Blender render job, as a dry run of the job's own command.
Called by tools/gpuq.sh for every Blender job, BEFORE the render starts (while the job waits for the GPU, on the CPU).

  python3 tools/collide_gate.py <job name> <command...>        (the same command gpuq.sh is about to run)
  exit 0 = pass (or not a Blender render, or the check could not run: said in the output), 3 = new visible penetration

How: the command is re-run with tools/collide_check.py loaded first (right after the .blend), so every render call the
job's scripts make (render3.py FRAMES, render_final.py animation, shots.py, -a / -f on the command line) becomes a check
of exactly that frame of exactly that scene. Nothing is rendered or saved (render and save calls are stubbed). Then
tools/collide_report.py groups the hits and applies the allowlists (collide_allow.txt next to the blend and up to 3
folders above, tools/collide_allow.txt).
Out: logs/collide/<time>-<job>.jsonl (per frame), .json (grouped hits), .txt (the report); a FAIL also appends one line to
logs/collide/FAILS.txt (gpuq.sh --status shows the last ones).
Env: COLLIDE=off skips; COLLIDE_STEP=N checks every Nth frame of an animation render (default 1 = every frame);
COLLIDE_PX (default 2) and COLLIDE_EPS (metres, default 0.01) as in collide_check/collide_report.
"""
import os, re, subprocess, sys, time, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC = os.path.join(ROOT, "tools", "collide_check.py")
REP = os.path.join(ROOT, "tools", "collide_report.py")


def is_blender(cmd):
    return bool(cmd) and os.path.basename(cmd[0]).lower() in ("blender", "blender.exe") and ("-b" in cmd or "--background" in cmd)


def dry_command(cmd):
    """Insert the hook after the .blend, turn CLI renders (-a / -f N) into render calls the hook intercepts."""
    try:
        sep = cmd.index("--")
    except ValueError:
        sep = len(cmd)
    head, tail = cmd[:sep], cmd[sep:]
    out, inserted, i = [], False, 0
    renders = []
    while i < len(head):
        a = head[i]
        if a in ("-a", "--render-anim"):
            renders.append(["--python-expr", "import bpy; bpy.ops.render.render(animation=True)"]); i += 1; continue
        if a in ("-f", "--render-frame") and i + 1 < len(head):
            for part in head[i + 1].split(","):
                if ".." in part:
                    x, y = part.split("..")
                    expr = (f"import bpy\nsc=bpy.context.scene\nfor f in range({int(x)},{int(y)}+1):\n"
                            f"    sc.frame_set(f); bpy.ops.render.render(write_still=True)")
                else:
                    f = part.lstrip("+")
                    expr = f"import bpy; bpy.context.scene.frame_set({int(f)}); bpy.ops.render.render(write_still=True)"
                renders.append(["--python-expr", expr])
            i += 2; continue
        out.append(a)
        if not inserted and (a.endswith(".blend") or (a in ("-b", "--background") and not (i + 1 < len(head) and head[i + 1].endswith(".blend")))):
            out += ["--python", CC]; inserted = True
        i += 1
    if not inserted:
        out[1:1] = ["--python", CC]
    for r in renders:
        out += r
    return out + tail


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    name, cmd = sys.argv[1], sys.argv[2:]
    if os.environ.get("COLLIDE", "warn") == "off" or not is_blender(cmd):
        return 0
    d = os.path.join(ROOT, "logs", "collide"); os.makedirs(d, exist_ok=True)
    stem = os.path.join(d, time.strftime("%Y%m%d-%H%M%S") + "-" + re.sub(r"[^A-Za-z0-9_.-]", "_", name))
    env = dict(os.environ, COLLIDE_OUT=stem + ".jsonl")
    t0 = time.time()
    with open(stem + ".blender.log", "w") as lo:
        rc = subprocess.run(dry_command(cmd), env=env, stdout=lo, stderr=subprocess.STDOUT, cwd=os.getcwd()).returncode
    if not os.path.exists(stem + ".jsonl"):
        print(f"[collide] {name}: no frame was checked (dry run rc={rc}, {time.time() - t0:.0f}s; the job may render nothing new, "
              f"or its scripts failed in the dry run: {stem}.blender.log)")
        return 0
    rp = subprocess.run([sys.executable, REP, stem + ".jsonl", "--label", name, "--json", stem + ".json",
                         "--px", os.environ.get("COLLIDE_PX", "2")], capture_output=True, text=True)
    open(stem + ".txt", "w").write(rp.stdout + rp.stderr)
    if rp.returncode == 3:
        bar = "!" * 100
        print(bar + "\n[collide] FAIL: objects cut through each other on screen in this render (her rule, Nov 7). Report: "
              + stem + ".txt\n" + rp.stdout + bar)
        with open(os.path.join(d, "FAILS.txt"), "a") as f:
            f.write(f"{time.strftime('%F %T')} {name}: {rp.stdout.splitlines()[0] if rp.stdout else ''} -> {stem}.txt\n")
        return 3
    print(rp.stdout.strip() + f" ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
