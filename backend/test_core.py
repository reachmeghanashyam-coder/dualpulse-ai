import numpy as np
import sys
import os

sys.path.append(os.path.dirname(__file__))
from vision_engine import ThreeTierClinicalVisionEngine
from agent_core import ArchivalHospitalAgent
from main import synthesize_night_icu_frame

def test_acuity_mode_drives_cv_rules():
    engine = ThreeTierClinicalVisionEngine()
    frame = synthesize_night_icu_frame(640, 480, 1, "NONE")
    
    # 1. Test High-Acuity ICU Mode: Tight bed perimeter
    engine.set_acuity_mode("HIGH_ACUITY_ICU")
    telemetry_icu = engine.process_frame(frame)
    assert telemetry_icu["acuity_mode"] == "HIGH_ACUITY_ICU"
    assert telemetry_icu["active_perimeter"] == engine.bed_perimeter_icu
    assert "line_sentinel" in telemetry_icu
    
    # 2. Test Step-Down Recovery Mode: Expanded spatial perimeter
    engine.set_acuity_mode("STEP_DOWN_RECOVERY")
    telemetry_recovery = engine.process_frame(frame)
    assert telemetry_recovery["acuity_mode"] == "STEP_DOWN_RECOVERY"
    assert telemetry_recovery["active_perimeter"] == engine.bed_perimeter_recovery

def test_closed_loop_opencv_conditioning_and_extubation():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_04")
    
    # Synthesize realistic dark ICU frame with specular monitor glare
    frame1 = synthesize_night_icu_frame(640, 480, 1, "EXTUBATION_ATTEMPT")
    frame2 = synthesize_night_icu_frame(640, 480, 2, "EXTUBATION_ATTEMPT")
    
    _ = engine.process_frame(frame1, simulated_event="EXTUBATION_ATTEMPT")
    telemetry = engine.process_frame(frame2, simulated_event="EXTUBATION_ATTEMPT")
    
    # Verify Closed-Loop OpenCV Conditioning improved perceptual quality J(I)
    cl = telemetry["closed_loop_vision"]
    assert cl["restored_metrics"]["quality_score_j"] > cl["raw_metrics"]["quality_score_j"], \
        f"Expected restored J ({cl['restored_metrics']['quality_score_j']}) > raw J ({cl['raw_metrics']['quality_score_j']})"
    assert cl["restored_metrics"]["glare_ratio_pct"] < cl["raw_metrics"]["glare_ratio_pct"], \
        "Expected specular monitor glare to be reduced by cv2.inpaint"
    assert len(cl["tools_executed"]) >= 1
    assert telemetry["video_frame_b64"] is not None and len(telemetry["video_frame_b64"]) > 1000
    
    # Verify Extubation Breach Detection
    assert telemetry["breach_type"] == "UNPLANNED_EXTUBATION_RISK"
    assert telemetry["line_sentinel"]["integrity_status"] == "CRITICAL_EXTUBATION_ATTEMPT"
    assert telemetry["line_sentinel"]["extubation_risk_score"] >= 90.0
    
    patient = {
        "name": "Robert Davis",
        "patient_id": "PT-8821",
        "diagnosis": "Post-Stroke Recovery / Neurological Care",
        "acuity_mode": "HIGH_ACUITY_ICU"
    }
    decision = agent.evaluate(telemetry, patient)
    
    dispatches = decision["dispatches"]
    assert any(d["tier"] == "TIER_1_BEDSIDE" for d in dispatches)
    t1 = next(d for d in dispatches if d["tier"] == "TIER_1_BEDSIDE")
    assert t1["action_type"] == "BEDSIDE_TONE_PULSE"
    assert t1["frequency_hz"] == 880
    assert any(d["tier"] == "TIER_2_WARD_CONSOLE" for d in dispatches)
    
    engine.reset_line_security()
    assert engine.total_interventions_logged == 1
    assert engine.line_integrity_status == "SECURE"

def test_false_alarm_abstention_on_blanket_shift():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_04")
    frame = synthesize_night_icu_frame(640, 480, 5, "BLANKET_SHIFT")
    
    telemetry = engine.process_frame(frame, simulated_event="BLANKET_SHIFT")
    assert telemetry["breach_type"] == "ABSTAINED_SAFE_MOTION"
    assert telemetry["status"] == "ABSTAINED_SAFE_MOTION"
    assert telemetry["closed_loop_vision"]["abstained_false_alarm"] is True
    assert telemetry["closed_loop_vision"]["total_false_alarms_abstained"] >= 1
    
    patient = {"name": "Robert Davis", "patient_id": "PT-8821"}
    decision = agent.evaluate(telemetry, patient)
    assert any(d["tier"] == "TIER_0_AGENT_ABSTENTION" for d in decision["dispatches"])

def test_archival_discharge_dossier():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_04")
    frame = synthesize_night_icu_frame(640, 480, 1, "NONE")
    
    patient = {
        "name": "Robert Davis",
        "patient_id": "PT-8821",
        "age": 68,
        "diagnosis": "Post-Stroke Recovery / Neurological Care",
        "diet": "NPO (Strict Fasting - Post-Op)",
        "medication_schedule": "Warfarin 5mg @ 22:00, Metoprolol 25mg @ 08:00"
    }
    telemetry = engine.process_frame(frame)
    dossier = agent.compile_archival_discharge_dossier(patient, telemetry)
    
    assert "sha256:" in dossier["cryptographic_proof"]["hash"]
    assert dossier["room_id"] == "ICU_BED_04"
    assert "100% Zero Dislodgement" in dossier["patient_clinical_summary"]["line_extubation_prevention_status"]

if __name__ == "__main__":
    test_acuity_mode_drives_cv_rules()
    test_closed_loop_opencv_conditioning_and_extubation()
    test_false_alarm_abstention_on_blanket_shift()
    test_archival_discharge_dossier()
    print("ALL DEEP CLINICAL & CLOSED-LOOP OPENCV TESTS PASSED (EXIT 0)")
