from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import numpy as np
import cv2
import json
import time
import base64

from vision_engine import ThreeTierClinicalVisionEngine
from agent_core import ArchivalHospitalAgent

app = FastAPI(title="DualPulse AI Clinical Triage System", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ThreeTierClinicalVisionEngine(fps=30.0)
agent = ArchivalHospitalAgent(room_id="ICU_BED_04")

class PatientProfile(BaseModel):
    patient_id: str = "PT-8821"
    name: str = "Robert Davis"
    age: int = 68
    diagnosis: str = "Post-Stroke Recovery / Neurological Care"
    acuity_mode: str = "HIGH_ACUITY_ICU"  # "HIGH_ACUITY_ICU" or "STEP_DOWN_RECOVERY"
    diet: str = "NPO (Strict Fasting - Post-Op)"
    allergies: str = "Penicillin, Latex"
    medication_schedule: str = "Warfarin 5mg @ 22:00, Metoprolol 25mg @ 08:00"
    fall_risk: str = "HIGH"
    status: str = "ADMITTED_ACTIVE"

active_patient = PatientProfile()

class AcuityUpdate(BaseModel):
    acuity_mode: str

class SimulationCommand(BaseModel):
    command: str  # "NORMAL", "EXTUBATION", "SEIZURE", "FALL", "AGITATION", "RESET"

class VideoSourceCommand(BaseModel):
    source: str  # "SIMULATION" or "WEBCAM"

sim_state = {
    "event": "NONE",
    "video_source": "SIMULATION"
}

webcam_cap = None

@app.get("/")
def read_root():
    return {
        "system": "DualPulse AI Clinical Triage Gateway",
        "patient": active_patient.name,
        "acuity_mode": active_patient.acuity_mode,
        "tripwire_perimeter": engine.bed_perimeter_icu if active_patient.acuity_mode == "HIGH_ACUITY_ICU" else engine.bed_perimeter_recovery,
        "line_integrity": engine.line_integrity_status,
        "status": active_patient.status
    }

@app.get("/api/patient/profile")
def get_patient_profile():
    return active_patient

@app.post("/api/patient/acuity")
def set_acuity_mode(update: AcuityUpdate):
    """Switch patient acuity profile: directly updates OpenCV 5 spatial boundaries."""
    active_patient.acuity_mode = update.acuity_mode
    engine.set_acuity_mode(update.acuity_mode)
    return {"status": "UPDATED", "acuity_mode": active_patient.acuity_mode}

@app.post("/api/patient/line_secure")
def secure_lines():
    """Nurse manual bedside intervention: secures lines and resets extubation risk."""
    engine.reset_line_security()
    return {
        "status": "LINE_SECURED",
        "line_integrity": engine.line_integrity_status,
        "total_interventions_logged": engine.total_interventions_logged
    }

@app.post("/api/patient/resolve")
def resolve_incident():
    """Attends to active breach, resets alarm state, and logs nurse intervention in audit trail."""
    now = time.time()
    last_breach = engine.active_breach_type
    
    # Mark resolved in agent audit trail
    agent.escalation_log.append({
        "event_id": f"RESOLVE-{int(now * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "breach_type": "RESOLVED_BY_NURSE",
        "resolved_incident": last_breach,
        "action_taken": "Bedside Attended & Bed Tripped Alarms Cleared by Nurse Sarah Jenkins, RN",
        "patient_id": active_patient.patient_id
    })
    
    # Reset engine and simulation state
    engine.reset_line_security()
    engine.active_breach_type = "NONE"
    engine.incident_duration = 0.0
    sim_state["event"] = "NONE"
    
    return {
        "status": "INCIDENT_RESOLVED",
        "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "assigned_nurse": "Nurse Sarah Jenkins, RN",
        "current_breach": "NONE"
    }

@app.post("/api/patient/discharge")
def discharge_patient():
    """Discharges patient, compiles final EHR dossier with SHA-256 hash, and purges session memory."""
    dummy_frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    latest_telemetry = engine.process_frame(dummy_frame)
    report = agent.compile_archival_discharge_dossier(active_patient.dict(), latest_telemetry)
    
    # Safe memory purge (Law 12)
    agent.escalation_log.clear()
    engine.active_breach_type = "NONE"
    sim_state["event"] = "NONE"
    
    return {
        "status": "SESSION_PURGED_CLEARED",
        "discharge_dossier": report
    }

@app.post("/api/video/source")
def set_video_source(cmd: VideoSourceCommand):
    """Switch video feed between synthetic clinical simulation and live local USB/Webcam feed."""
    global webcam_cap
    sim_state["video_source"] = cmd.source
    
    if cmd.source == "WEBCAM":
        if webcam_cap is None or not webcam_cap.isOpened():
            webcam_cap = cv2.VideoCapture(0)
    else:
        if webcam_cap is not None and webcam_cap.isOpened():
            webcam_cap.release()
            webcam_cap = None
            
    return {
        "status": "SOURCE_UPDATED",
        "video_source": sim_state["video_source"],
        "camera_ready": bool(webcam_cap and webcam_cap.isOpened()) if cmd.source == "WEBCAM" else True
    }

@app.post("/api/eval/simulate")
def set_simulation(cmd: SimulationCommand):
    """1-Click Evaluation Mode for Judges: Normal, Extubation, Seizure, Fall, Agitation."""
    if cmd.command == "EXTUBATION":
        sim_state["event"] = "EXTUBATION_ATTEMPT"
    elif cmd.command in ["SEIZURE", "FALL", "AGITATION"]:
        sim_state["event"] = cmd.command
    else:
        sim_state["event"] = "NONE"
        engine.reset_line_security()
        engine.active_breach_type = "NONE"
        engine.incident_duration = 0.0
        
    return {
        "status": "ACKNOWLEDGED",
        "command": cmd.command,
        "active_simulated_event": sim_state["event"]
    }

@app.get("/api/benchmarks/cool")
def get_cool_benchmarks():
    import os
    results_path = os.path.join(os.path.dirname(__file__), "cool_benchmark_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return {"error": "Benchmark not executed"}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    w, h = 640, 480
    frame_idx = 0
    
    try:
        while True:
            frame_idx += 1
            global webcam_cap
            
            # Choose frame source: live physical camera vs synthetic simulation
            if sim_state["video_source"] == "WEBCAM" and webcam_cap is not None and webcam_cap.isOpened():
                ret, live_frame = webcam_cap.read()
                if ret and live_frame is not None:
                    frame = cv2.resize(live_frame, (w, h))
                else:
                    frame = np.full((h, w, 3), 20, dtype=np.uint8)
            else:
                frame = np.full((h, w, 3), 20, dtype=np.uint8)
                
                # Position simulation based on event
                if sim_state["event"] == "SEIZURE":
                    shake_x = int(np.sin(frame_idx * 1.5) * 18)
                    shake_y = int(np.cos(frame_idx * 1.5) * 18)
                    px, py = 320 + shake_x, 240 + shake_y
                elif sim_state["event"] == "FALL":
                    px, py = 320, 440
                elif sim_state["event"] == "AGITATION":
                    px = 320 + int(np.sin(frame_idx * 0.4) * 22)
                    py = 240 + int(np.cos(frame_idx * 0.4) * 8)
                else:
                    px, py = 320, 240
                    
                # Draw synthetic patient & bed frame
                cv2.rectangle(frame, (120, 90), (520, 390), (50, 50, 25), 2)
                cv2.ellipse(frame, (px, py), (70, 110), 0, 0, 360, (180, 160, 140), -1)
                cv2.circle(frame, (px, py - 90), 40, (200, 180, 160), -1)
            
            # 1. OpenCV 5 Adaptive Vision Engine
            telemetry = engine.process_frame(frame, simulated_event=sim_state["event"])
            
            # If in WEBCAM mode, stream compressed JPEG video frame for live canvas rendering
            if sim_state["video_source"] == "WEBCAM":
                # Annotate optical flow ROI tripwires onto live frame for visual proof
                annotated = frame.copy()
                cv2.rectangle(annotated, (120, 90), (520, 390), (0, 229, 255), 2) # Bed perimeter tripwire
                cv2.rectangle(annotated, (280, 150), (360, 210), (0, 0, 255) if telemetry.get("active_breach") == "UNPLANNED_EXTUBATION_RISK" else (255, 200, 0), 2)
                cv2.putText(annotated, "OPENCV 5 AIRWAY TRIPWIRE", (240, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 229, 255), 1)
                
                _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 55])
                telemetry["video_frame_b64"] = base64.b64encode(buffer).decode('utf-8')
                telemetry["is_live_camera"] = True
            else:
                telemetry["is_live_camera"] = False
            
            # 2. Multi-Tier Clinical Agent
            agent_decision = agent.evaluate(telemetry, active_patient.dict())
            telemetry["agent"] = agent_decision
            telemetry["patient"] = active_patient.dict()
            telemetry["server_time"] = time.time()
            
            await websocket.send_json(telemetry)
            await asyncio.sleep(1.0 / 30.0)
            
    except WebSocketDisconnect:
        print("[*] Telemetry client disconnected")
