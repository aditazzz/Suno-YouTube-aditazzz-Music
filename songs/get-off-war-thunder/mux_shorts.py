# Adds the song (with short fades) to the three silent Short renders. In the chat this ran as an inline script.
# Run in this folder after the three `python3 vertical.py <k> short_<k>_v.mp4` renders finish.
import subprocess, json
S={"1":(9.6,45.8,"1 - Owen Get Off War Thunder"),"2":(45.8,77.5,"2 - Alexs Spotter Guide"),"3":(77.5,120.56,"3 - Moms Coming Around")}
for k,(a,b,name) in S.items():
    dur=b-a
    out=f"Get Off War Thunder - Short {name}.mp4"   # the chat wrote to /mnt/user-data/outputs/
    cmd=["ffmpeg","-v","error","-y","-i",f"short_{k}_v.mp4","-ss",f"{a:.3f}","-t",f"{dur:.3f}","-i","song.wav",
         "-map","0:v","-map","1:a","-af",f"afade=t=in:st=0:d=0.25,afade=t=out:st={dur-0.5:.3f}:d=0.5",
         "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",out]
    subprocess.run(cmd,check=True)
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height","-of","json",out],capture_output=True,text=True)
    print(name, json.loads(p.stdout)["format"]["duration"])
