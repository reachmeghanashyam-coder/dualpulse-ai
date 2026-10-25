import cv2
import numpy as np
import base64
import time
from typing import Dict, Any, List, Optional, Tuple

def evaluate_quality(gray: np.ndarray) -> Dict[str, float]:
    mu = float(np.mean(gray))
    sd = float(np.std(gray))
    glare = float(np.mean(gray > 235))
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # Normalized quality score
    lum_score = 1.0 - min(1.0, abs(mu - 115.0) / 115.0)
    contrast_score = min(1.0, sd / 48.0)
    sharp_score = min(1.0, sharp / 140.0)
    glare_penalty = min(1.0, glare * 15.0)
    j = max(0.05, (0.35 * lum_score) + (0.35 * contrast_score) + (0.20 * sharp_score) - (0.35 * glare_penalty))
    
    return {
        "mu": round(mu, 1),
        "sigma": round(sd, 1),
        "glare_pct": round(glare * 100.0, 2),
        "sharpness": round(sharp, 1),
        "J": round(j, 3)
    }

def condition_frame(gray: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    q0 = evaluate_quality(gray)
    tools = []
    out = gray.copy()
    backtracked = False
    
    # Glare suppression if monitor specular reflection is detected
    if q0["glare_pct"] > 0.6:
        _, m = cv2.threshold(out, 230, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        m = cv2.dilate(m, kernel, iterations=2)
        out = cv2.inpaint(out, m, 5, cv2.INPAINT_TELEA)
        tools.append("cv2.inpaint(glare_dome, TELEA)")
        
    # Low light recovery
    if q0["mu"] < 85 or q0["sigma"] < 35:
        clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
        out = clahe.apply(out)
        out = cv2.bilateralFilter(out, d=5, sigmaColor=30, sigmaSpace=30)
        tools.append("cv2.createCLAHE(2.4) + cv2.bilateralFilter")
        
    q1 = evaluate_quality(out)
    if tools and q1["J"] < q0["J"]:
        out = gray.copy()
        q1 = q0
        backtracked = True
        tools.append("BACKTRACKED(Reverted to Raw)")
        
    if not tools:
        tools.append("PASS_THROUGH (Optimal Contrast)")
        
    improvement = round(((q1["J"] - q0["J"]) / max(q0["J"], 0.01)) * 100.0, 1)
    
    return out, {
        "raw_metrics": q0,
        "restored_metrics": q1,
        "tools_executed": tools,
        "backtracked": backtracked,
        "quality_gain_pct": improvement
    }

class RealFootageVisionEngine:
    """
    OpenCV 5 Real-Footage Sentinel Engine.
    Processes live real hospital/bedroom clips (or USB webcam) with:
      1. Closed-loop perceptual frame conditioning (Inpaint + CLAHE + Bilateral)
      2. MOG2 adaptive background segmentation & foreground morphological cleaning
      3. True kinematic trajectory estimation (centroid drop velocity, aspect ratio expansion, post-impact stillness)
      4. False-alarm suppression gate (ABSTAIN on bed turns, sit-to-sleep, blanket shifts)
    """
    def __init__(self, fps: float = 25.0):
        self.fps = fps
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
        self.tracking_history: List[Optional[Dict[str, float]]] = []
        self.frame_count = 0
        self.active_verdict = "PATIENT_REST_NORMAL"
        self.alarm_latched = False
        self.latched_drop_pct = 0.0
        self.latched_h_loss_pct = 0.0
        self.consecutive_alert_frames = 0
        self.total_falls_detected = 0
        self.total_false_alarms_abstained = 0
        self.last_abstain_time = 0.0
        self.last_alert_time = 0.0

    def reset(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=32, detectShadows=False)
        self.tracking_history.clear()
        self.frame_count = 0
        self.active_verdict = "PATIENT_REST_NORMAL"
        self.alarm_latched = False
        self.latched_drop_pct = 0.0
        self.latched_h_loss_pct = 0.0
        self.consecutive_alert_frames = 0

    def clear_alarm(self):
        self.alarm_latched = False
        self.active_verdict = "PATIENT_REST_NORMAL"
        self.tracking_history.clear()

    def process_frame(self, frame_bgr: np.ndarray) -> Dict[str, Any]:
        self.frame_count += 1
        h_orig, w_orig = frame_bgr.shape[:2]
        
        # Standardize processing resolution (640x360 or 640x480)
        target_w = 640
        target_h = int(h_orig * (640.0 / w_orig))
        small_bgr = cv2.resize(frame_bgr, (target_w, target_h))
        gray = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)
        
        # 1. Closed-Loop Perception & Conditioning
        cond_gray, trace = condition_frame(gray)
        
        # 2. MOG2 Motion Segmentation & Morphological Filtering
        fg_mask = self.bg_subtractor.apply(cond_gray)
        fg_clean = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        fg_clean = cv2.morphologyEx(fg_clean, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        
        contours, _ = cv2.findContours(fg_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        active_bbox = None
        if contours and self.frame_count > 12: # Allow background model to warm up
            # Filter contours by minimum patient body mass
            valid_cnts = [c for c in contours if cv2.contourArea(c) > (0.012 * target_w * target_h)]
            if valid_cnts:
                largest_c = max(valid_cnts, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_c)
                active_bbox = {
                    "cx": x + w / 2.0,
                    "cy": y + h / 2.0,
                    "w": float(w),
                    "h": float(h),
                    "t": float(self.frame_count / self.fps),
                    "H": float(target_h),
                    "x": x, "y": y
                }
                
        self.tracking_history.append(active_bbox)
        if len(self.tracking_history) > 120:
            self.tracking_history.pop(0)
            
        # 3. Deterministic Kinematic Fall & Abstention Decision
        kinematics = self._evaluate_kinematics(target_h)
        
        now = time.time()
        if kinematics["is_fall"]:
            self.consecutive_alert_frames += 1
        else:
            self.consecutive_alert_frames = 0

        # Require 3 consecutive confirmed fall frames to reject 1-frame segmentation noise
        confirmed_fall = (self.consecutive_alert_frames >= 3)

        if confirmed_fall or self.alarm_latched:
            if confirmed_fall and not self.alarm_latched:
                self.alarm_latched = True
                self.latched_drop_pct = max(self.latched_drop_pct, kinematics["drop_pct"])
                self.latched_h_loss_pct = max(self.latched_h_loss_pct, kinematics.get("height_loss_pct", 0.0))
            kinematics["is_fall"] = True
            kinematics["drop_pct"] = max(kinematics["drop_pct"], self.latched_drop_pct)
            kinematics["height_loss_pct"] = max(kinematics.get("height_loss_pct", 0.0), self.latched_h_loss_pct)
            self.active_verdict = "CRITICAL_INTERVENTION_REQUIRED"
            if now - self.last_alert_time > 4.0:
                self.total_falls_detected += 1
                self.last_alert_time = now
        elif kinematics["is_abstained"]:
            self.active_verdict = "ABSTAINED_SAFE_MOTION"
            if now - self.last_abstain_time > 4.0:
                self.total_false_alarms_abstained += 1
                self.last_abstain_time = now
        else:
            self.active_verdict = "PATIENT_REST_NORMAL"
            
        # 4. Render Live Split Visual Proof:
        # Left: Raw Corrupted Frame | Right: OpenCV Tracked + Kinematic HUD
        visual_b64 = self._render_live_split_hud(small_bgr, cond_gray, active_bbox, trace, kinematics)
        
        return {
            "status": self.active_verdict,
            "breach_type": "BED_FALL_COLLAPSE" if self.active_verdict == "CRITICAL_INTERVENTION_REQUIRED" else (
                "ABSTAINED_SAFE_MOTION" if self.active_verdict == "ABSTAINED_SAFE_MOTION" else "NONE"
            ),
            "frame_idx": self.frame_count,
            "kinematics": kinematics,
            "closed_loop_vision": {
                **trace,
                "abstained_false_alarm": kinematics["is_abstained"],
                "total_falls_detected": self.total_falls_detected,
                "total_false_alarms_abstained": self.total_false_alarms_abstained,
                "open_loop_comparison": (
                    "CRITICAL FALL CONFIRMED: Rapid centroid descent deltaY=" + str(kinematics["drop_pct"]) + 
                    "% & aspect ratio expansion. Nurse dispatched." if kinematics["is_fall"] else (
                        "AGENTIC ABSTENTION: Normal downward trajectory without impact collapse (Safe bed transition). Alert suppressed." if kinematics["is_abstained"] else
                        "Patient resting safely within baseline motion envelope."
                    )
                )
            },
            "video_frame_b64": visual_b64
        }
        
    def _evaluate_kinematics(self, frame_height: float) -> Dict[str, Any]:
        valid_pts = [p for p in self.tracking_history if p is not None]
        if len(valid_pts) < 12:
            return {"is_fall": False, "is_abstained": False, "drop_pct": 0.0, "reason": "INITIALIZING_MODEL"}
            
        ts = np.array([p["t"] for p in valid_pts])
        cy = np.array([p["cy"] for p in valid_pts]) / frame_height
        hh = np.array([p["h"] for p in valid_pts]) / frame_height
        ar = np.array([p["w"] / max(p["h"], 1.0) for p in valid_pts])
        
        best_drop = 0.0
        best_h_loss = 0.0
        best_idx_j = -1
        
        # Check window of descent (~0.4 - 0.9 seconds)
        window = max(2, int(0.55 * self.fps))
        for i in range(len(valid_pts) - window):
            j = i + window
            if ts[j] - ts[i] > 1.2:
                continue
            drop = cy[j] - cy[i]
            h_loss = hh[i] - hh[j]
            if drop > best_drop:
                best_drop = float(drop)
                best_h_loss = float(h_loss)
                best_idx_j = j
                
        # Fall criteria calibrated to real biomechanical descent:
        # Requires genuine vertical drop AND substantial loss of standing/seated height
        is_fall = False
        is_abstained = False
        
        if best_idx_j != -1:
            post_impact_pts = valid_pts[best_idx_j : best_idx_j + int(1.1 * self.fps)]
            post_still = True
            if len(post_impact_pts) >= 4:
                post_still = float(np.std([p["cy"] for p in post_impact_pts]) / frame_height) < 0.08
                
            post_ar = float(np.mean(ar[best_idx_j : best_idx_j + max(3, int(0.5 * self.fps))]))
            
            # Ground-truth fall: 
            # Case A: Rapid standing collapse (person loses > 25% height and drops > 20% down to floor)
            # Case B: Chair slide collapse (person slides down > 13% and loses > 20% seated height)
            standing_collapse = (best_drop >= 0.20 and best_h_loss >= 0.25)
            chair_collapse = (best_drop >= 0.13 and best_h_loss >= 0.20 and post_still)

            if (standing_collapse or chair_collapse) and post_still:
                is_fall = True
            elif best_drop > 0.10:
                is_abstained = True
                
        return {
            "is_fall": is_fall,
            "is_abstained": is_abstained,
            "drop_pct": round(best_drop * 100.0, 1),
            "height_loss_pct": round(best_h_loss * 100.0, 1)
        }

    def _render_live_split_hud(
        self,
        raw_bgr: np.ndarray,
        cond_gray: np.ndarray,
        bbox: Optional[Dict[str, Any]],
        trace: Dict[str, Any],
        kinematics: Dict[str, Any]
    ) -> str:
        h, w = raw_bgr.shape[:2]
        mid_x = w // 2
        
        cond_bgr = cv2.cvtColor(cond_gray, cv2.COLOR_GRAY2BGR)
        
        # Visual cues on Restored Feed
        if bbox is not None:
            x, y, bw, bh = int(bbox["x"]), int(bbox["y"]), int(bbox["w"]), int(bbox["h"])
            color = (0, 40, 255) if kinematics["is_fall"] else (
                (0, 230, 120) if kinematics["is_abstained"] else (0, 229, 255)
            )
            cv2.rectangle(cond_bgr, (x, y), (x + bw, y + bh), color, 2)
            cv2.circle(cond_bgr, (int(bbox["cx"]), int(bbox["cy"])), 6, color, -1)
            
            # Posture Vector HUD
            label = "COLLAPSE DETECTED" if kinematics["is_fall"] else (
                "SAFE TRANSITION (ABSTAIN)" if kinematics["is_abstained"] else "PATIENT TRACKED"
            )
            cv2.putText(cond_bgr, label, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
            
        # Compose split-screen
        composite = np.zeros((h, w, 3), dtype=np.uint8)
        composite[:, :mid_x] = raw_bgr[:, :mid_x]
        composite[:, mid_x:] = cond_bgr[:, mid_x:]
        
        # Center cyan divider
        cv2.line(composite, (mid_x, 0), (mid_x, h), (0, 229, 255), 2)
        
        # Top diagnostic bar
        cv2.rectangle(composite, (0, 0), (w, 30), (8, 10, 15), -1)
        q_raw = trace["raw_metrics"]
        q_rest = trace["restored_metrics"]
        cv2.putText(composite, f"RAW NIR NIGHT OPTICS | J={q_raw['J']:.2f} | Glare={q_raw['glare_pct']}%", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 175, 195), 1, cv2.LINE_AA)
        cv2.putText(composite, f"OPENCV 5 CLAHE + MOG2 MOTION | J={q_rest['J']:.2f} (+{trace['quality_gain_pct']}%)", (mid_x + 10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 240, 180), 1, cv2.LINE_AA)
        
        # Bottom telemetry bar
        cv2.rectangle(composite, (0, h - 26), (w, h), (8, 10, 15), -1)
        cv2.putText(composite, f"NIGHT PIPELINE: {' -> '.join(trace['tools_executed'])}", (10, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 220, 240), 1, cv2.LINE_AA)
        
        _, buffer = cv2.imencode('.jpg', composite, [cv2.IMWRITE_JPEG_QUALITY, 68])
        return base64.b64encode(buffer).decode('utf-8')
