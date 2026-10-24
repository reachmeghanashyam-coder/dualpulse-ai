import numpy as np
import sys
import os

sys.path.append(os.path.dirname(__file__))
from vision_engine import ThreeTierClinicalVisionEngine
from agent_core import ArchivalHospitalAgent

def test_acuity_mode_drives_cv_rules():
    engine = ThreeTierClinicalVisionEngine()
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    
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

def test_life_support_line_extubation_interception():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_04")
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    
    # Simulate ICU delirium hand reaching for endotracheal airway tube
    telemetry = engine.process_frame(frame, simulated_event="EXTUBATION_ATTEMPT")
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
    
    # Check that reassuring bedside voice was triggered
    dispatches = decision["dispatches"]
    assert any(d["tier"] == "TIER_1_BEDSIDE" for d in dispatches)
    t1 = next(d for d in dispatches if d["tier"] == "TIER_1_BEDSIDE")
    assert "you're safe. Nurse Sarah is on her way" in t1["voice_prompt"]
    
    # Check that Tier 2 STAT Nurse Dispatch was transmitted
    assert any(d["tier"] == "TIER_2_WARD_CONSOLE" for d in dispatches)
    
    # Nurse resets line security
    engine.reset_line_security()
    assert engine.total_interventions_logged == 1
    assert engine.line_integrity_status == "SECURE"

def test_archival_discharge_dossier():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_04")
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    
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
    test_life_support_line_extubation_interception()
    test_archival_discharge_dossier()
    print("ALL DEEP CLINICAL TESTS PASSED (EXIT 0)")
