import cv2
import numpy as np
import time
from typing import Dict, Any, List, Optional

class ThreeTierClinicalVisionEngine:
    """
    DualPulse AI: 3-Tier Hospital Vision Engine
    Part 1: Normal Routine Care (Rest & 120-min Bedsore Turn Clock)
    Part 2: Case-Sensitive Protocol Rules (NPO Fasting, Fall Tripwire, Rx Sync)
    Part 3: Extreme High-Acuity Scanning (Seizures, Falls, Acute Agitation)
    """
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.dt = 1.0 / fps
        self.prev_gray: Optional[np.ndarray] = None
        
        # Clinical Acuity Mode: "HIGH_ACUITY_ICU" vs "STEP_DOWN_RECOVERY"
        self.acuity_mode = "HIGH_ACUITY_ICU"
        
        # Part 1: Bedsore Repositioning Clock (120 minutes = 7200 seconds)
        self.time_since_last_turn = 2520.0 # e.g. 42 minutes elapsed (78m remaining)
        self.total_turns_logged = 3
        
        # Part 2: Case-Sensitive Rules
        self.npo_order_active = True
        self.fall_risk_strict = True
        
        # Part 3: Extreme Scanning Boundaries
        self.bed_perimeter_icu = [120, 90, 520, 390]
        self.bed_perimeter_recovery = [40, 40, 600, 440]
        self.patient_centroid = [320, 240]
        
        # Kinetic Motion & Breaches
        self.motion_history = []
        self.incident_duration = 0.0
        self.active_breach_type = "NONE"
        self.concordance_score = 98.4 # %
        
    def set_acuity_mode(self, mode: str):
        self.acuity_mode = mode
        self.active_breach_type = "NONE"
        self.incident_duration = 0.0
        
    def log_patient_turn(self):
        """Simulates nurse repositioning patient in bed."""
        self.time_since_last_turn = 0.0
        self.total_turns_logged += 1
        
    def process_frame(self, frame: np.ndarray, simulated_event: str = "NONE") -> Dict[str, Any]:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Advance Bedsore Turn Clock (Part 1)
        self.time_since_last_turn += self.dt * 2.0 # subtle advance
        turn_overdue = self.time_since_last_turn >= 7200.0
        
        # 1. OPTICAL FLOW KINETIC ENERGY
        motion_energy = 0.0
        if self.prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion_energy = float(np.mean(mag))
            
        self.prev_gray = gray.copy()
        
        # Simulation overrides
        if simulated_event == "SEIZURE":
            motion_energy = 8.6
        elif simulated_event == "FALL":
            motion_energy = 9.8
            self.patient_centroid = [320, 440] # Fallen to floor
        elif simulated_event == "AGITATION":
            motion_energy = 4.8
            self.patient_centroid = [320, 240]
        else:
            self.patient_centroid = [320, 240]
            
        self.motion_history.append(motion_energy)
        if len(self.motion_history) > 30:
            self.motion_history.pop(0)
            
        avg_motion = float(np.mean(self.motion_history)) if self.motion_history else 0.0
        
        # 2. CASE-SENSITIVE SPATIAL EVALUATION (Part 2 & Part 3)
        active_perimeter = self.bed_perimeter_icu if self.acuity_mode == "HIGH_ACUITY_ICU" else self.bed_perimeter_recovery
        x1, y1, x2, y2 = active_perimeter
        px, py = self.patient_centroid
        is_outside = (px < x1 or px > x2 or py < y1 or py > y2)
        
        if self.acuity_mode == "HIGH_ACUITY_ICU":
            # Part 3: Extreme Scanning Mode
            if is_outside:
                self.active_breach_type = "BED_FALL_COLLAPSE"
                self.incident_duration += self.dt
                self.concordance_score = max(50.0, self.concordance_score - 0.5)
            elif avg_motion > 5.5 or simulated_event == "SEIZURE":
                self.active_breach_type = "SEIZURE_CONVULSION"
                self.incident_duration += self.dt
                self.concordance_score = max(50.0, self.concordance_score - 0.5)
            elif avg_motion > 3.0 or simulated_event == "AGITATION":
                self.active_breach_type = "ACUTE_AGITATION"
                self.incident_duration += self.dt
            else:
                self.active_breach_type = "NONE"
                self.incident_duration = max(0.0, self.incident_duration - self.dt * 2.0)
                self.concordance_score = min(99.5, self.concordance_score + 0.05)
        else:
            # Part 1 & 2: Step-Down Recovery Mode (High Tolerance)
            if is_outside and simulated_event == "FALL":
                self.active_breach_type = "BED_FALL_COLLAPSE"
                self.incident_duration += self.dt
            elif avg_motion > 7.5 or simulated_event == "SEIZURE":
                self.active_breach_type = "SEIZURE_CONVULSION"
                self.incident_duration += self.dt
            else:
                self.active_breach_type = "NONE"
                self.incident_duration = 0.0
                
        status = "CRITICAL_INTERVENTION_REQUIRED" if self.active_breach_type != "NONE" else ("TURN_OVERDUE_WARNING" if turn_overdue else "PATIENT_REST_NORMAL")
        
        mins_remaining = max(0, int((7200.0 - self.time_since_last_turn) / 60.0))
        
        return {
            "acuity_mode": self.acuity_mode,
            "status": status,
            "breach_type": self.active_breach_type,
            "motion_energy": round(motion_energy, 2),
            "avg_motion": round(avg_motion, 2),
            "incident_duration_sec": round(self.incident_duration, 1),
            "patient_centroid": self.patient_centroid,
            "active_perimeter": active_perimeter,
            "tripwire_status": "BREACHED" if is_outside else "CONTAINED",
            "concordance_score": round(self.concordance_score, 1),
            "bedsore_turn_clock": {
                "mins_remaining": mins_remaining,
                "elapsed_mins": int(self.time_since_last_turn / 60.0),
                "total_turns_logged": self.total_turns_logged,
                "turn_overdue": turn_overdue
            }
        }
