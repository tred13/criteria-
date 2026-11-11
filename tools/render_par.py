import os, sys
from multiprocessing import Pool
import renderer

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frames")

def work(f):
    renderer.frame(f).save(os.path.join(OUT, "f%04d.png" % f))
    return f

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    e = int(sys.argv[2]) if len(sys.argv) > 2 else renderer.TOTAL
    renderer.assets()
    with Pool(processes=min(8, os.cpu_count() or 4)) as p:
        for i, f in enumerate(p.imap_unordered(work, range(n, e), chunksize=6)):
            if i % 90 == 0:
                print("done", i, flush=True)
    print("ALL DONE")
