"""Evaluate fall_tracker on GMDCSA24 (CC BY 4.0). Ground truth = folder (Fall vs ADL) + CSV event times."""
import cv2, os, sys, glob, json, re, csv, time
from concurrent.futures import ProcessPoolExecutor
sys.path.append(os.path.dirname(__file__))
from fall_tracker import FallTracker

ROOT = glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "gmdcsa24", "*"))[0]


def run_clip(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    tr = FallTracker(fps)
    tools = set()
    n = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out = tr.update(f)
        tools.update(out["trace"]["tools"])
        n += 1
    cap.release()
    d = tr.decide()
    d["frames"] = n
    d["conditioning_tools"] = sorted(tools)
    return path, d


def fall_start(csv_path, fname):
    with open(csv_path, encoding="utf-8", errors="ignore") as fh:
        for row in csv.reader(fh):
            if row and row[0].strip() == fname:
                m = re.search(r"Fall\w*\s*(?:\([A-Za-z]+\))?\s*\[\s*([\d.]+)\s*to", row[-1])
                lighting = row[2].strip() if len(row) > 2 else ""
                return (float(m.group(1)) if m else None), lighting
    return None, ""


if __name__ == "__main__":
    clips = []
    for p in sorted(glob.glob(os.path.join(ROOT, "Subject *", "*", "*.mp4"))):
        kind = os.path.basename(os.path.dirname(p))
        clips.append((p, kind))
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as ex:
        results = list(ex.map(run_clip, [c[0] for c in clips]))
    kinds = dict(clips)
    tp = fn = fp = tn = 0
    rows = []
    lat = []
    for p, d in results:
        kind = kinds[p]
        pred_fall = d["verdict"] == "FALL_ESCALATE"
        subj = os.path.basename(os.path.dirname(os.path.dirname(p)))
        csvp = os.path.join(os.path.dirname(os.path.dirname(p)), f"{kind}.csv")
        gt_t, light = fall_start(csvp, os.path.basename(p))
        if kind == "Fall":
            if pred_fall:
                tp += 1
                if gt_t is not None:
                    lat.append(d["t_event"] - gt_t)
            else:
                fn += 1
        else:
            if pred_fall:
                fp += 1
            else:
                tn += 1
        rows.append({"clip": f"{subj}/{kind}/{os.path.basename(p)}", "truth": kind, "light": light,
                     "gt_fall_start": gt_t, **d})
    n_f, n_a = tp + fn, fp + tn
    summary = {
        "clips": len(results), "falls": n_f, "adl": n_a,
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,
        "fall_recall": round(tp / max(n_f, 1), 3),
        "adl_false_alarm_rate": round(fp / max(n_a, 1), 3),
        "precision": round(tp / max(tp + fp, 1), 3),
        "median_detect_minus_gt_start_s": sorted(lat)[len(lat) // 2] if lat else None,
        "seconds": round(time.time() - t0, 1),
    }
    out = {"summary": summary, "clips": rows}
    with open(os.path.join(os.path.dirname(__file__), "eval_results.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(summary, indent=1))
