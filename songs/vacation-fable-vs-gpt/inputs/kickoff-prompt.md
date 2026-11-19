Make a music video, following AGENTS.md, for the film in films/vacation-to-my-bed/.

Stages 0, 1 and 2 are already done: the song is final, mastered, and every sung word is timed (song/). Read these first, in this order: films/vacation-to-my-bed/direction.md (the full direction, approved by the person; it is the brief), prompt.md, run.json, log.md, then tendencies.md. Start at stage 3 (pipeline/3-treatment.md) and follow the direction.

The setup for this run:
- Time limit: 4 hours from run.json "started", final render included. Plan for it from the start (pipeline/6-build.md, "Time"). Run `python3 tools/clock.py films/vacation-to-my-bed` to check.
- Nobody will answer questions or leave notes during the run, and there is no WIP. Make every decision yourself and keep going until the film is finished or the time is up. Write WIP-style entries as Markdown files in the film folder instead.
- Do not open Suno or make, download or change any song: the song is final.
- Do not call any other AI model's tools or CLIs (no `codex`, no `claude`). Your own helpers and critic are fine.
- Stay inside this repository folder. Free CC0 assets (for example Poly Haven) are fine for set dressing; log each one in assets.md.
- Deliver the finished film to films/vacation-to-my-bed/renders/final/ as film.mp4 (1920x1080, 30 fps, H.264, the master audio, exactly the master's length), with the report pipeline/7-edit.md asks for.
