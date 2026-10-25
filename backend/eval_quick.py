import cv2, os, sys, glob, time
cv2.setNumThreads(1)
sys.path.append(os.path.dirname(__file__))
from fall_tracker import FallTracker

ROOT = glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "gmdcsa24", "*"))[0]
subj = sys.argv[1] if len(sys.argv) > 1 else "Subject 1"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

for kind in ["Fall", "ADL"]:
    for p in sorted(glob.glob(os.path.join(ROOT, subj, kind, "*.mp4")))[:n]:
        t0 = time.time()
        cap = cv2.VideoCapture(p)
        tr = FallTracker(cap.get(cv2.CAP_PROP_FPS) or 25)
        tools = set()
        while True:
            ok, f = cap.read()
            if not ok:
                break
            tools.update(tr.update(f)["trace"]["tools"])
        d = tr.decide()
        print(f"{kind:4} {os.path.basename(p)} -> {d['verdict']:22} {d}  tools={sorted(tools)}  {time.time()-t0:.1f}s")
