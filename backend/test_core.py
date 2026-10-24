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
    assert "bedsore_turn_clock" in telemetry_icu
    
    # 2. Test Step-Down Recovery Mode: Expanded spatial perimeter
    engine.set_acuity_mode("STEP_DOWN_RECOVERY")
    telemetry_recovery = engine.process_frame(frame)
    assert telemetry_recovery["acuity_mode"] == "STEP_DOWN_RECOVERY"
    assert telemetry_recovery["active_perimeter"] == engine.bed_perimeter_recovery

def test_bedsore_turn_clock_and_nurse_logging():
    engine = ThreeTierClinicalVisionEngine()
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    
    # Force turn clock to overdue (>120 mins = 7200s)
    engine.time_since_last_turn = 7300.0
    telemetry = engine.process_frame(frame)
    assert telemetry["bedsore_turn_clock"]["turn_overdue"] is True
    assert telemetry["bedsore_turn_clock"]["mins_remaining"] == 0
    
    # Nurse logs turn
    engine.log_patient_turn()
    assert engine.total_turns_logged == 4
    assert engine.time_since_last_turn == 0.0
    telemetry_after = engine.process_frame(frame)
    assert telemetry_after["bedsore_turn_clock"]["turn_overdue"] is False
    assert telemetry_after["bedsore_turn_clock"]["mins_remaining"] >= 119

def test_seizure_and_multi_tier_dispatch():
    engine = ThreeTierClinicalVisionEngine()
    agent = ArchivalHospitalAgent(room_id="ICU_BED_TEST")
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    
    # Simulate seizure convulsion
    telemetry = engine.process_frame(frame, simulated_event="SEIZURE")
    assert telemetry["breach_type"] == "SEIZURE_CONVULSION"
    
    patient = {
        "name": "Robert Davis",
        "patient_id": "PT-8821",
        "diagnosis": "Post-Stroke Recovery",
        "acuity_mode": "HIGH_ACUITY_ICU"
    }
    decision = agent.evaluate(telemetry, patient)
    
    # Check that Tier 1 (Bedside voice) and Tier 2 (Ward console) dispatched
    dispatches = decision["dispatches"]
    assert any(d["tier"] == "TIER_1_BEDSIDE" for d in dispatches)
    assert any(d["tier"] == "TIER_2_WARD_CONSOLE" for d in dispatches)
    
    # Check Discharge dossier compiling with SHA-256
    dossier = agent.compile_archival_discharge_dossier(patient, telemetry)
    assert "sha256:" in dossier["cryptographic_proof"]["hash"]
    assert dossier["room_id"] == "ICU_BED_TEST"
    assert "100% Verified" in dossier["patient_clinical_summary"]["bedsore_prevention_compliance"]

if __name__ == "__main__":
    test_acuity_mode_drives_cv_rules()
    test_bedsore_turn_clock_and_nurse_logging()
    test_seizure_and_multi_tier_dispatch()
    print("ALL DEEP CLINICAL TESTS PASSED (EXIT 0)")
