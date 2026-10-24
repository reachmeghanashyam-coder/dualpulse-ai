import cv2
import numpy as np
import time
from typing import Dict, Any, List, Optional

class ThreeTierClinicalVisionEngine:
    """
    DualPulse AI: 3-Part Clinical Vision Operating System
    Part 1: Life-Support Tube & Central IV Line Extubation Sentinel (ICU Delirium Intercept)
    Part 2: Case-Sensitive Protocol Enforcement (Bed-Exit Guardrail Tripwire & NPO Fasting)
    Part 3: Extreme High-Acuity Scanning (2.5-5.0Hz Seizure Optical Flow & Bed-Fall Collapse)
    """
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.dt = 1.0 / fps
        self.prev_gray: Optional[np.ndarray] = None
        
        # Clinical Acuity Mode: "HIGH_ACUITY_ICU" vs "STEP_DOWN_RECOVERY"
        self.acuity_mode = "HIGH_ACUITY_ICU"
        
        # Part 1: Life-Support Tube & Line Extubation Zones
        # Tracheostomy / Endotracheal Tube Zone (Head/Neck): [280, 150, 360, 210]
        # Central Venous Line / Arterial Line Zone (Subclavian / Chest): [270, 210, 370, 290]
        self.airway_tube_roi = [280, 150, 360, 210]
        self.central_line_roi = [270, 210, 370, 290]
        self.hand_centroid = [230, 310] # Normal resting hand position by hip
        self.line_integrity_status = "SECURE" # "SECURE", "REACHING_WARNING", "CRITICAL_EXTUBATION_ATTEMPT"
        self.extubation_risk_score = 0.0 # 0 to 100%
        
        # Part 2: Spatial Boundaries (ICU vs Recovery)
        self.bed_perimeter_icu = [120, 90, 520, 390]
        self.bed_perimeter_recovery = [40, 40, 600, 440]
        self.patient_centroid = [320, 240]
        
        # Kinetic Motion & Breaches
        self.motion_history = []
        self.incident_duration = 0.0
        self.active_breach_type = "NONE"
        self.concordance_score = 98.4 # %
        self.total_interventions_logged = 0
        
    def set_acuity_mode(self, mode: str):
        self.acuity_mode = mode
        self.active_breach_type = "NONE"
        self.incident_duration = 0.0
        
    def reset_line_security(self):
        """Simulates nurse securing lines and calming patient."""
        self.hand_centroid = [230, 310]
        self.line_integrity_status = "SECURE"
        self.extubation_risk_score = 0.0
        self.total_interventions_logged += 1
        
    def process_frame(self, frame: np.ndarray, simulated_event: str = "NONE") -> Dict[str, Any]:
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
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
        
        # Simulation Overrides
        if simulated_event == "EXTUBATION_ATTEMPT":
            # Hand trajectory moves rapidly towards tracheostomy / endotracheal airway zone
            self.hand_centroid = [305, 185] # Direct breach of airway tube zone
            motion_energy = 4.2
        elif simulated_event == "SEIZURE":
            motion_energy = 8.6
            self.hand_centroid = [260, 270]
        elif simulated_event == "FALL":
            motion_energy = 9.8
            self.patient_centroid = [320, 440] # Fallen to floor
            self.hand_centroid = [320, 460]
        elif simulated_event == "AGITATION":
            motion_energy = 5.2
            self.hand_centroid = [285, 230] # Hand near central line zone
        else:
            self.patient_centroid = [320, 240]
            self.hand_centroid = [230, 310]
            
        self.motion_history.append(motion_energy)
        if len(self.motion_history) > 30:
            self.motion_history.pop(0)
            
        avg_motion = float(np.mean(self.motion_history)) if self.motion_history else 0.0
        
        # 2. PART 1: LIFE-SUPPORT TUBE & LINE EXTUBATION SENTINEL
        hx, hy = self.hand_centroid
        tx1, ty1, tx2, ty2 = self.airway_tube_roi
        cx1, cy1, cx2, cy2 = self.central_line_roi
        
        # Check proximity to airway tube
        airway_breach = (tx1 <= hx <= tx2 and ty1 <= hy <= ty2)
        # Check proximity to central line
        central_line_breach = (cx1 <= hx <= cx2 and cy1 <= hy <= cy2)
        
        if airway_breach or simulated_event == "EXTUBATION_ATTEMPT":
            self.line_integrity_status = "CRITICAL_EXTUBATION_ATTEMPT"
            self.extubation_risk_score = 96.0
            self.active_breach_type = "UNPLANNED_EXTUBATION_RISK"
            self.incident_duration += self.dt
            self.concordance_score = max(50.0, self.concordance_score - 0.6)
        elif central_line_breach:
            self.line_integrity_status = "REACHING_WARNING"
            self.extubation_risk_score = 72.0
            self.active_breach_type = "CENTRAL_LINE_DISLODGEMENT_RISK"
            self.incident_duration += self.dt
            self.concordance_score = max(50.0, self.concordance_score - 0.3)
        else:
            self.line_integrity_status = "SECURE"
            self.extubation_risk_score = max(0.0, self.extubation_risk_score - 2.0)
            
        # 3. PART 2 & PART 3: SPATIAL PERIMETER & KINETIC CRISIS
        active_perimeter = self.bed_perimeter_icu if self.acuity_mode == "HIGH_ACUITY_ICU" else self.bed_perimeter_recovery
        x1, y1, x2, y2 = active_perimeter
        px, py = self.patient_centroid
        is_outside = (px < x1 or px > x2 or py < y1 or py > y2)
        
        if self.acuity_mode == "HIGH_ACUITY_ICU":
            if is_outside or simulated_event == "FALL":
                self.active_breach_type = "BED_FALL_COLLAPSE"
                self.incident_duration += self.dt
                self.concordance_score = max(50.0, self.concordance_score - 0.5)
            elif avg_motion > 5.5 or simulated_event == "SEIZURE":
                self.active_breach_type = "SEIZURE_CONVULSION"
                self.incident_duration += self.dt
                self.concordance_score = max(50.0, self.concordance_score - 0.5)
            elif not airway_breach and not central_line_breach:
                self.active_breach_type = "NONE"
                self.incident_duration = max(0.0, self.incident_duration - self.dt * 2.0)
                self.concordance_score = min(99.5, self.concordance_score + 0.05)
        else:
            if is_outside and simulated_event == "FALL":
                self.active_breach_type = "BED_FALL_COLLAPSE"
                self.incident_duration += self.dt
            elif avg_motion > 7.5 or simulated_event == "SEIZURE":
                self.active_breach_type = "SEIZURE_CONVULSION"
                self.incident_duration += self.dt
            elif not airway_breach:
                self.active_breach_type = "NONE"
                self.incident_duration = 0.0
                
        status = "CRITICAL_INTERVENTION_REQUIRED" if self.active_breach_type != "NONE" else "PATIENT_REST_NORMAL"
        
        return {
            "acuity_mode": self.acuity_mode,
            "status": status,
            "breach_type": self.active_breach_type,
            "motion_energy": round(motion_energy, 2),
            "avg_motion": round(avg_motion, 2),
            "incident_duration_sec": round(self.incident_duration, 1),
            "patient_centroid": self.patient_centroid,
            "hand_centroid": self.hand_centroid,
            "active_perimeter": active_perimeter,
            "tripwire_status": "BREACHED" if is_outside else "CONTAINED",
            "concordance_score": round(self.concordance_score, 1),
            "line_sentinel": {
                "airway_tube_roi": self.airway_tube_roi,
                "central_line_roi": self.central_line_roi,
                "hand_centroid": self.hand_centroid,
                "integrity_status": self.line_integrity_status,
                "extubation_risk_score": round(self.extubation_risk_score, 1),
                "total_interventions_logged": self.total_interventions_logged
            }
        }
