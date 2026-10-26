from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import numpy as np
import cv2
import json
import time
import os

import base64
from real_vision_engine import RealFootageVisionEngine
from agent_core import ArchivalHospitalAgent

app = FastAPI(title="DualPulse AI Real Bed Fall Sentinel", version="4.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RealFootageVisionEngine(fps=25.0)
agent = ArchivalHospitalAgent(room_id="WARD_BED_04")

class PatientProfile(BaseModel):
    patient_id: str = "PT-8821"
    name: str = "Robert Davis"
    age: int = 68
    diagnosis: str = "Post-Stroke Recovery / Bed Fall Risk"
    acuity_mode: str = "HIGH_ACUITY_ICU"
    diet: str = "NPO (Strict Fasting - Post-Op)"
    allergies: str = "Penicillin, Latex"
    medication_schedule: str = "Warfarin 5mg @ 22:00, Metoprolol 25mg @ 08:00"
    fall_risk: str = "HIGH"
    status: str = "ADMITTED_ACTIVE"

active_patient = PatientProfile()

class ClipCommand(BaseModel):
    clip_id: str  # "FALL_STANDING", "FALL_CHAIR", "WEBCAM", "STANDBY"

CURRENT_STATE = {
    "clip_id": "STANDBY",
    "video_source": "STANDBY"
}

CLIP_MAP = {
    "FALL_STANDING": "sample_walking_fall.mp4",
    "FALL_CHAIR": "sample_fall.mp4"
}

CLIP_WARMUP = {
    "FALL_CHAIR": 0,
    "FALL_STANDING": 0
}

current_cap = None
webcam_cap = None

def render_standby_hud() -> str:
    frame = np.full((360, 640, 3), 12, dtype=np.uint8)
    for gy in range(0, 360, 30):
        cv2.line(frame, (0, gy), (640, gy), (22, 26, 36), 1)
    for gx in range(0, 640, 30):
        cv2.line(frame, (gx, 0), (gx, 360), (22, 26, 36), 1)
        
    cx, cy = 320, 155
    cv2.circle(frame, (cx, cy), 50, (0, 229, 255), 1)
    cv2.circle(frame, (cx, cy), 4, (0, 229, 255), -1)
    cv2.line(frame, (cx - 70, cy), (cx - 15, cy), (0, 229, 255), 1)
    cv2.line(frame, (cx + 15, cy), (cx + 70, cy), (0, 229, 255), 1)
    cv2.line(frame, (cx, cy - 70), (cx, cy - 15), (0, 229, 255), 1)
    cv2.line(frame, (cx, cy + 15), (cx, cy + 70), (0, 229, 255), 1)
    
    corners = [(30, 30), (610, 30), (30, 330), (610, 330)]
    for x, y in corners:
        dx = 15 if x == 30 else -15
        dy = 15 if y == 30 else -15
        cv2.line(frame, (x, y), (x + dx, y), (0, 240, 180), 2)
        cv2.line(frame, (x, y), (x, y + dy), (0, 240, 180), 2)
        
    cv2.rectangle(frame, (0, 0), (640, 28), (8, 10, 15), -1)
    cv2.putText(frame, "DUALPULSE AI // AWS GRAVITON4 OPENCV 5 SENTINEL", (15, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 229, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "STANDBY MODE // READY FOR TRIGGER", (370, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 240, 180), 1, cv2.LINE_AA)
    
    cv2.putText(frame, "PATIENT SENTINEL ARMED", (cx - 110, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "Click [1. Standing Transfer Fall] or [2. Bedside Chair Fall] to Play", (cx - 235, 268), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 229, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, "Live video streaming and kinematic evaluation will begin from 0.0s upon click.", (cx - 245, 292), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 155, 175), 1, cv2.LINE_AA)
    
    cv2.rectangle(frame, (0, 336), (640, 360), (8, 10, 15), -1)
    cv2.putText(frame, "STATUS: STANDBY // CAMERA FEED READY // ZERO FALSE ALARMS", (15, 352), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 175, 195), 1, cv2.LINE_AA)

    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
    return base64.b64encode(buffer).decode('utf-8')

def get_clip_cap(clip_id: str):
    backend_dir = os.path.dirname(__file__)
    filename = CLIP_MAP.get(clip_id, "sample_fall.mp4")
    path = os.path.join(backend_dir, filename)
    if os.path.exists(path):
        cap = cv2.VideoCapture(path)
        warmup = CLIP_WARMUP.get(clip_id, 0)
        for _ in range(warmup):
            ret, f = cap.read()
            if ret and f is not None:
                engine.process_frame(f)
        return cap
    return None

@app.get("/")
def read_root():
    return {
        "system": "DualPulse AI Hospital Bed Fall Sentinel",
        "clip": CURRENT_STATE["clip_id"],
        "source": CURRENT_STATE["video_source"]
    }

@app.post("/api/eval/clip")
def set_clip(cmd: ClipCommand):
    global current_cap, webcam_cap
    engine.reset()
    agent.reset()
    CURRENT_STATE["clip_id"] = cmd.clip_id
    
    if cmd.clip_id == "STANDBY":
        CURRENT_STATE["video_source"] = "STANDBY"
        if webcam_cap is not None:
            webcam_cap.release()
            webcam_cap = None
        if current_cap is not None:
            current_cap.release()
            current_cap = None
    elif cmd.clip_id == "WEBCAM":
        CURRENT_STATE["video_source"] = "WEBCAM"
        if current_cap is not None:
            current_cap.release()
            current_cap = None
        if webcam_cap is None or not webcam_cap.isOpened():
            webcam_cap = cv2.VideoCapture(0)
    else:
        CURRENT_STATE["video_source"] = "REAL_DATASET"
        if webcam_cap is not None:
            webcam_cap.release()
            webcam_cap = None
        if current_cap is not None:
            current_cap.release()
        current_cap = get_clip_cap(cmd.clip_id)
        
    return {
        "status": "LOADED",
        "clip_id": CURRENT_STATE["clip_id"],
        "source": CURRENT_STATE["video_source"]
    }

@app.post("/api/patient/resolve")
def resolve_incident():
    global current_cap
    now = time.time()
    agent.escalation_log.append({
        "event_id": f"RESOLVE-{int(now * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "breach_type": "RESOLVED_BY_NURSE",
        "action_taken": "Bedside Attended & Bed Tripped Alarms Cleared by Nurse Sarah Jenkins, RN",
        "patient_id": active_patient.patient_id
    })
    engine.reset()
    agent.reset()
    if current_cap is not None:
        current_cap.release()
    current_cap = get_clip_cap(CURRENT_STATE["clip_id"])
    return {"status": "RESOLVED", "current_breach": "NONE"}

@app.post("/api/patient/discharge")
def discharge_patient():
    dummy = np.full((360, 640, 3), 40, dtype=np.uint8)
    latest_telemetry = engine.process_frame(dummy)
    dossier = agent.compile_archival_discharge_dossier(active_patient.dict(), latest_telemetry)
    agent.escalation_log.clear()
    engine.reset()
    return {"status": "PURGED", "discharge_dossier": dossier}

@app.get("/api/benchmarks/cool")
def get_cool_benchmarks():
    results_path = os.path.join(os.path.dirname(__file__), "cool_benchmark_results.json")
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            return json.load(f)
    return {"error": "Benchmark missing"}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    global current_cap, webcam_cap
    await websocket.accept()
    
    if current_cap is None and CURRENT_STATE["video_source"] == "REAL_DATASET":
        current_cap = get_clip_cap(CURRENT_STATE["clip_id"])
        
    try:
        while True:
            if CURRENT_STATE["clip_id"] == "STANDBY":
                b64_frame = render_standby_hud()
                telemetry = {
                    "status": "SENTINEL_STANDBY",
                    "breach_type": "NONE",
                    "frame_idx": 0,
                    "kinematics": {"is_fall": False, "is_abstained": False, "drop_pct": 0.0, "height_loss_pct": 0.0},
                    "closed_loop_vision": {
                        "raw_metrics": {"J": 0.50, "glare_pct": 0.0},
                        "restored_metrics": {"J": 0.85},
                        "quality_gain_pct": 70.0,
                        "tools_executed": ["STANDBY_READY"],
                        "abstained_false_alarm": False,
                        "total_falls_detected": 0,
                        "total_false_alarms_abstained": 0,
                        "open_loop_comparison": "Sentinel armed in standby. Click a scenario button to begin live stream."
                    },
                    "video_frame_b64": b64_frame,
                    "agent": {"dispatches": []},
                    "patient": active_patient.dict(),
                    "clip_info": {
                        "active_clip": "STANDBY",
                        "source": "STANDBY",
                        "dataset_citation": "GMDCSA24 (CC BY 4.0)"
                    }
                }
                await websocket.send_json(telemetry)
                await asyncio.sleep(0.1)
                continue

            frame = None
            if CURRENT_STATE["video_source"] == "WEBCAM" and webcam_cap is not None and webcam_cap.isOpened():
                ret, live_f = webcam_cap.read()
                if ret and live_f is not None:
                    frame = live_f
            elif current_cap is not None and current_cap.isOpened():
                ret, video_f = current_cap.read()
                if not ret or video_f is None:
                    current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, video_f = current_cap.read()
                    engine.reset()
                    agent.reset()
                if ret and video_f is not None:
                    frame = video_f
                    
            if frame is None:
                frame = np.full((360, 640, 3), 30, dtype=np.uint8)
                cv2.putText(frame, "Awaiting Camera / Video Feed...", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                
            telemetry = engine.process_frame(frame)
            agent_decision = agent.evaluate(telemetry, active_patient.dict())
            telemetry["agent"] = agent_decision
            telemetry["patient"] = active_patient.dict()
            telemetry["clip_info"] = {
                "active_clip": CURRENT_STATE["clip_id"],
                "source": CURRENT_STATE["video_source"],
                "dataset_citation": "GMDCSA24 (CC BY 4.0)"
            }
            
            await websocket.send_json(telemetry)
            await asyncio.sleep(1.0 / 25.0)
            
    except WebSocketDisconnect:
        pass
