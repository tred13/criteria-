"""tools/mux.py — assemble frames + optional audio into the delivery MP4s.

Runs on GitHub Actions (see .github/workflows/render.yml). Never in the agent sandbox.
"""
import argparse
import glob
import os
import subprocess

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default="frames", help="folder holding f0000.png ...")
    ap.add_argument("--out", default="out", help="output folder")
    ap.add_argument("--audio", default=None, help="optional voice-over file")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1080x1920")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    first = sorted(glob.glob(os.path.join(a.frames, "f*.png")))[0]
    pattern = os.path.join(a.frames, "f%04d.png") if "%04d" in first.replace("f0000", "f%04d") \
        else os.path.join(a.frames, "f%04d.png")

    master = os.path.join(a.out, "why-is-the-sky-blue.mp4")
    share = os.path.join(a.out, "why-is-the-sky-blue-share.mp4")
    dur = str(len(glob.glob(os.path.join(a.frames, "f*.png"))) / float(a.fps))

    cmd = [FF, "-y", "-loglevel", "warning", "-framerate", str(a.fps), "-i", pattern]
    if a.audio:
        # pad the narration with silence so the film keeps its full length
        cmd += ["-i", a.audio,
                "-filter_complex", "[1:a]apad[a]", "-map", "0:v", "-map", "[a]",
                "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-preset", "medium", "-t", dur, master]
    subprocess.run(cmd, check=True)

    w, h = a.size.split("x")
    subprocess.run([FF, "-y", "-loglevel", "warning", "-i", master,
                    "-vf", "scale=%d:%d" % (int(w) // 2 * 1, int(h) // 2 * 1),
                    "-c:v", "libx264", "-crf", "24", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", share], check=True)

    for f in (master, share):
        print(f, round(os.path.getsize(f) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
