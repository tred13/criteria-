"""tools/mux.py — assemble frames + voice-over into the delivery MP4s."""
import os
import subprocess
import sys

import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FRAMES = os.path.join(ROOT, "frames")
VO = os.path.join(ROOT, "voiceover.mp3")
OUT = os.path.join(HERE, "..", "render")

FF = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(OUT, exist_ok=True)


def run(args):
    print(" ".join(args[:6]), "...")
    subprocess.run(args, check=True)


master = os.path.join(OUT, "why-is-the-sky-blue.mp4")
share = os.path.join(OUT, "why-is-the-sky-blue-share.mp4")

run([FF, "-y", "-loglevel", "warning", "-framerate", "30",
     "-i", os.path.join(FRAMES, "f%04d.png"), "-i", VO,
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
     "-c:a", "aac", "-b:a", "160k", "-t", "30", master])

run([FF, "-y", "-loglevel", "warning", "-i", master, "-vf", "scale=720:1280",
     "-c:v", "libx264", "-crf", "24", "-preset", "medium",
     "-c:a", "aac", "-b:a", "128k", share])

for f in (master, share):
    print(f, round(os.path.getsize(f) / 1e6, 1), "MB")
