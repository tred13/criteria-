"""tools/render_par.py — parallel frame renderer (GitHub Actions only).

    python3 tools/render_par.py [start] [count] [outdir]
"""
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import renderer  # noqa: E402


def work(job):
    f, out = job
    renderer.frame(f).save(os.path.join(out, "f%04d.png" % f))
    return f


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else renderer.TOTAL
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.abspath(
        os.path.join(HERE, "..", "frames"))
    os.makedirs(out, exist_ok=True)
    renderer.assets()
    jobs = [(f, out) for f in range(start, start + count)]
    n = min(8, os.cpu_count() or 4)
    with Pool(processes=n) as p:
        for i, _ in enumerate(p.imap_unordered(work, jobs, chunksize=4)):
            if i % 50 == 0:
                print("frame %d / %d" % (i, len(jobs)), flush=True)
    print("DONE", len(jobs), "frames ->", out)


if __name__ == "__main__":
    main()
