"""
Real-footage fall tracker (OpenCV only, no hardcoded outcomes).

Pipeline per frame:
  1. PERCEIVE  - measure luminance / contrast / glare / sharpness on the real frame.
  2. CONDITION - CLAHE (+ glare inpaint) only if the measurement says the frame is poor,
                 then RE-MEASURE; keep the result only if quality improved (else backtrack).
  3. TRACK     - MOG2 background subtraction -> largest moving contour -> bbox, centroid.
  4. DECIDE    - fall = fast downward centroid drop + bbox turns wide (aspect) + stillness after.
                 Anything else with motion is ABSTAINED (daily activity).
"""
import cv2
import numpy as np
from typing import Dict, Any, List


def quality(gray: np.ndarray) -> Dict[str, float]:
    mu = float(gray.mean())
    sd = float(gray.std())
    glare = float((gray > 235).mean())
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    lum = 1.0 - min(1.0, abs(mu - 115.0) / 115.0)
    j = 0.4 * lum + 0.4 * min(1.0, sd / 48.0) + 0.2 * min(1.0, sharp / 140.0) - 0.35 * min(1.0, glare * 12.0)
    return {"mu": mu, "sigma": sd, "glare": glare, "sharp": sharp, "J": max(0.0, j)}


def condition(gray: np.ndarray):
    """Closed loop: act only if needed, verify, backtrack if not better."""
    q0 = quality(gray)
    tools: List[str] = []
    out = gray
    if q0["glare"] > 0.006:
        _, m = cv2.threshold(out, 230, 255, cv2.THRESH_BINARY)
        m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=2)
        out = cv2.inpaint(out, m, 5, cv2.INPAINT_TELEA)
        tools.append("inpaint_glare")
    if q0["mu"] < 85 or q0["sigma"] < 35:
        out = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8)).apply(out)
        tools.append("clahe")
    q1 = quality(out)
    backtracked = False
    if tools and q1["J"] <= q0["J"]:
        out, q1, backtracked = gray, q0, True
        tools.append("BACKTRACK")
    return out, {"before": q0, "after": q1, "tools": tools, "backtracked": backtracked}


class FallTracker:
    def __init__(self, fps: float):
        self.fps = fps
        self.bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
        self.hist: List[Dict[str, float]] = []   # per-frame bbox stats
        self.frames = 0

    def update(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        small = cv2.resize(frame_bgr, (320, int(frame_bgr.shape[0] * 320 / frame_bgr.shape[1])))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        cond, trace = condition(gray)
        fg = self.bg.apply(cond)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.frames += 1
        rec = None
        if cnts and self.frames > 15:  # let background model settle
            c = max(cnts, key=cv2.contourArea)
            if cv2.contourArea(c) > 0.01 * gray.size:
                x, y, w, h = cv2.boundingRect(c)
                rec = {"cx": x + w / 2, "cy": y + h / 2, "w": w, "h": h, "t": self.frames / self.fps,
                       "H": gray.shape[0]}
        self.hist.append(rec)
        return {"bbox": rec, "trace": trace, "fg": fg, "gray": cond}

    def decide(self) -> Dict[str, Any]:
        """Offline/over-window decision using only tracked geometry."""
        pts = [r for r in self.hist if r]
        if len(pts) < 10:
            return {"verdict": "ABSTAIN_NO_SUBJECT", "reason": "subject not tracked"}
        H = pts[0]["H"]
        ts = np.array([p["t"] for p in pts])
        cy = np.array([p["cy"] for p in pts]) / H
        ar = np.array([p["w"] / max(p["h"], 1) for p in pts])
        hh = np.array([p["h"] for p in pts]) / H
        best = {"drop": 0.0}
        win = max(2, int(0.6 * self.fps))
        for i in range(len(pts) - win):
            # centroid drop within ~0.6 s, normalised by frame height
            j = i + win
            if ts[j] - ts[i] > 1.0:
                continue
            drop = cy[j] - cy[i]
            height_loss = hh[i] - hh[j]
            if drop > best["drop"]:
                best = {"drop": float(drop), "height_loss": float(height_loss), "i": i, "j": j}
        if best["drop"] <= 0 or "j" not in best:
            return {"verdict": "ABSTAIN_SAFE_ACTIVITY", "reason": "no rapid descent"}
        j = best["j"]
        tail = pts[j:j + int(1.0 * self.fps)]
        still = True
        if len(tail) > 3:
            still = float(np.std([p["cy"] for p in tail]) / H) < 0.03
        wide_after = float(np.mean(ar[j:j + max(3, int(0.5 * self.fps))])) > 1.0
        is_fall = best["drop"] > 0.12 and best["height_loss"] > 0.12 and wide_after and still
        return {
            "verdict": "FALL_ESCALATE" if is_fall else "ABSTAIN_SAFE_ACTIVITY",
            "drop": round(best["drop"], 3), "height_loss": round(best["height_loss"], 3),
            "wide_after": wide_after, "still_after": still,
            "t_event": round(float(ts[j]), 2),
        }
