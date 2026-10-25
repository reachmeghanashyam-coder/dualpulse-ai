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

app = FastAPI(title="DualPulse AI Clinical Triage System", version="3.2.0")

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
    command: str  # "NORMAL", "EXTUBATION", "SEIZURE", "FALL", "AGITATION", "BLANKET_SHIFT", "RESET"

class VideoSourceCommand(BaseModel):
    source: str  # "SIMULATION" or "WEBCAM"

sim_state = {
    "event": "NONE",
    "video_source": "SIMULATION"
}

webcam_cap = None


def synthesize_night_icu_frame(w: int, h: int, frame_idx: int, event: str) -> np.ndarray:
    """
    Synthesizes a 640x480 night-time ICU bed frame with realistic optical degradations:
    - Low ambient night-ward illumination (mean pixel luminance ~26-38)
    - Textured hospital mattress, bed rails, pillow, endotracheal tube, and patient anatomy
    - Specular glare dome from a bedside vitals monitor (pixel saturation > 240)
    - Thermal sensor noise and scenario-specific anatomical trajectories
    """
    rng = np.random.default_rng(seed=(frame_idx % 97) + 101)
    frame = np.full((h, w, 3), 14, dtype=np.uint8)

    # Subtle floor tile grid in dark room
    for gx in range(80, 560, 48):
        cv2.line(frame, (gx, 0), (gx, h), (19, 20, 22), 1)
    for gy in range(40, h, 48):
        cv2.line(frame, (80, gy), (560, gy), (19, 20, 22), 1)

    # Bed frame and dark mattress
    cv2.rectangle(frame, (120, 80), (520, 400), (30, 32, 36), -1)
    cv2.rectangle(frame, (120, 80), (520, 400), (48, 52, 58), 2)
    # Pillow at head of bed
    cv2.rectangle(frame, (235, 92), (405, 165), (46, 48, 52), -1)

    # Determine patient torso (px, py) and hand (hx, hy) coordinates by scenario
    hx, hy = 230, 310
    px, py = 320, 245

    if event == "EXTUBATION_ATTEMPT":
        # Hand sweeps upward toward endotracheal tube at neck
        osc = int(np.sin(frame_idx * 0.45) * 9)
        hx, hy = 312 + osc, 172 - abs(osc)
        px, py = 320, 240
    elif event == "SEIZURE":
        shake_x = int(np.sin(frame_idx * 1.65) * 20)
        shake_y = int(np.cos(frame_idx * 1.65) * 16)
        px, py = 320 + shake_x, 242 + shake_y
        hx, hy = 265 + shake_x, 255 - shake_y
    elif event == "FALL":
        # Patient swings across right/bottom bed perimeter onto floor
        drift = int(np.sin(frame_idx * 0.35) * 10)
        px, py = 320 + drift, 432
        hx, hy = 335 + drift, 452
    elif event in ["AGITATION", "BLANKET_SHIFT"]:
        # Benign blanket shift / torso roll inside safe bed center (Abstention Test)
        shift_x = int(np.sin(frame_idx * 0.55) * 24)
        shift_y = int(np.cos(frame_idx * 0.55) * 12)
        px, py = 320 + shift_x, 248 + shift_y
        hx, hy = 245 + int(shift_x * 0.6), 298 + int(shift_y * 0.5)
    else:
        # Normal breathing micro-motion
        breath = int(np.sin(frame_idx * 0.15) * 3)
        px, py = 320, 242 + breath
        hx, hy = 230, 310

    # Patient torso & blanket folds (low-contrast night luminance so CLAHE visibly restores it)
    cv2.ellipse(frame, (px, py + 20), (74, 105), 0, 0, 360, (54, 58, 62), -1)
    # Blanket texture ribs so Farneback optical flow has rich spatial gradients once CLAHE runs
    for r_offset in range(-65, 75, 18):
        cv2.line(frame, (px - 58, py + 20 + r_offset), (px + 58, py + 25 + r_offset), (68, 72, 76), 2)

    # Patient head & facial features
    head_y = min(py - 92, 165) if event != "FALL" else py - 70
    cv2.circle(frame, (px, head_y), 36, (66, 70, 74), -1)

    # Endotracheal airway tube & central line catheter
    cv2.line(frame, (220, 115), (318, 172), (82, 86, 92), 3)
    cv2.circle(frame, (318, 172), 6, (95, 100, 105), -1)

    # Patient active arm & hand
    cv2.line(frame, (px - 45, py - 15), (hx, hy), (64, 68, 72), 14)
    cv2.circle(frame, (hx, hy), 14, (78, 82, 88), -1)

    # Realistic Optical Failure Mode 1: Specular Glare Dome from Bedside Vitals Monitor
    # Placed over the upper-left airway/head zone to blind naive open-loop trackers
    glare_layer = np.zeros_like(frame)
    cv2.circle(glare_layer, (265, 168), 38, (252, 252, 255), -1)
    cv2.circle(glare_layer, (185, 130), 26, (245, 245, 250), -1)
    glare_layer = cv2.GaussianBlur(glare_layer, (25, 25), 9.0)
    frame = cv2.add(frame, glare_layer)

    # Realistic Optical Failure Mode 2: Slight motion blur on seizure + sensor shot noise
    if event == "SEIZURE":
        frame = cv2.GaussianBlur(frame, (5, 5), 1.4)

    noise = rng.integers(-6, 7, size=(h, w, 1), dtype=np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return frame


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
    
    agent.escalation_log.append({
        "event_id": f"RESOLVE-{int(now * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "breach_type": "RESOLVED_BY_NURSE",
        "resolved_incident": last_breach,
        "action_taken": "Bedside Attended & Bed Tripped Alarms Cleared by Nurse Sarah Jenkins, RN",
        "patient_id": active_patient.patient_id
    })
    
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
    dummy_frame = synthesize_night_icu_frame(640, 480, 1, "NONE")
    latest_telemetry = engine.process_frame(dummy_frame, encode_visual=False)
    report = agent.compile_archival_discharge_dossier(active_patient.dict(), latest_telemetry)
    
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
    """1-Click Evaluation Mode for Judges: Normal, Extubation, Seizure, Fall, Blanket_Shift (Abstention)."""
    if cmd.command == "EXTUBATION":
        sim_state["event"] = "EXTUBATION_ATTEMPT"
    elif cmd.command in ["SEIZURE", "FALL", "AGITATION", "BLANKET_SHIFT"]:
        sim_state["event"] = "BLANKET_SHIFT" if cmd.command in ["AGITATION", "BLANKET_SHIFT"] else cmd.command
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
            
            is_live_cam = False
            if sim_state["video_source"] == "WEBCAM" and webcam_cap is not None and webcam_cap.isOpened():
                ret, live_frame = webcam_cap.read()
                if ret and live_frame is not None:
                    frame = cv2.resize(live_frame, (w, h))
                    is_live_cam = True
                else:
                    frame = synthesize_night_icu_frame(w, h, frame_idx, sim_state["event"])
            else:
                frame = synthesize_night_icu_frame(w, h, frame_idx, sim_state["event"])
            
            # 1. Closed-Loop OpenCV 5 Vision Engine (Perceive -> Condition -> Verify -> Track -> Decide/Abstain)
            # Encode split-screen visual proof every 2nd frame (~15 FPS visual stream, 30 FPS telemetry)
            encode_now = (frame_idx % 2 == 0) or (frame_idx == 1)
            telemetry = engine.process_frame(frame, simulated_event=sim_state["event"], encode_visual=encode_now)
            if not encode_now and hasattr(engine, "_last_b64"):
                telemetry["video_frame_b64"] = engine._last_b64
            else:
                engine._last_b64 = telemetry.get("video_frame_b64")

            telemetry["is_live_camera"] = is_live_cam
            
            # 2. Multi-Tier Clinical Agent (Escalates hazards or logs False-Alarm Abstention)
            agent_decision = agent.evaluate(telemetry, active_patient.dict())
            telemetry["agent"] = agent_decision
            telemetry["patient"] = active_patient.dict()
            telemetry["server_time"] = time.time()
            
            await websocket.send_json(telemetry)
            await asyncio.sleep(1.0 / 30.0)
            
    except WebSocketDisconnect:
        print("[*] Telemetry client disconnected")
