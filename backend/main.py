from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import numpy as np
import cv2
import json
import time
import os
import glob

from real_vision_engine import RealFootageVisionEngine
from agent_core import ArchivalHospitalAgent

app = FastAPI(title="DualPulse AI Real-Footage Clinical Sentinel", version="4.0.0")

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
    diagnosis: str = "Post-Stroke Recovery / Fall-Risk Protocol"
    acuity_mode: str = "HIGH_ACUITY_ICU"
    diet: str = "NPO (Strict Fasting - Post-Op)"
    allergies: str = "Penicillin, Latex"
    medication_schedule: str = "Warfarin 5mg @ 22:00, Metoprolol 25mg @ 08:00"
    fall_risk: str = "HIGH"
    status: str = "ADMITTED_ACTIVE"

active_patient = PatientProfile()

class ClipCommand(BaseModel):
    clip_id: str  # "FALL_CHAIR", "FALL_BED", "ADL_SLEEP", "ADL_TURN", "WEBCAM"

CURRENT_STATE = {
    "clip_id": "FALL_CHAIR",
    "video_source": "REAL_DATASET" # or "WEBCAM"
}

CLIP_MAP = {
    "FALL_CHAIR": "sample_fall.mp4",
    "FALL_BED": "sample_fall_2.mp4",
    "ADL_SLEEP": "sample_adl.mp4",
    "ADL_TURN": "sample_adl_2.mp4"
}

current_cap = None
webcam_cap = None

def get_clip_cap(clip_id: str):
    backend_dir = os.path.dirname(__file__)
    filename = CLIP_MAP.get(clip_id, "sample_fall.mp4")
    path = os.path.join(backend_dir, filename)
    if os.path.exists(path):
        cap = cv2.VideoCapture(path)
        return cap
    return None

@app.get("/")
def read_root():
    return {
        "system": "DualPulse AI Real-Footage Sentinel",
        "dataset": "GMDCSA24 (CC BY 4.0 Verified Real Human Bedroom Footage)",
        "current_clip": CURRENT_STATE["clip_id"],
        "source": CURRENT_STATE["video_source"]
    }

@app.post("/api/eval/clip")
def set_clip(cmd: ClipCommand):
    global current_cap, webcam_cap
    engine.reset()
    CURRENT_STATE["clip_id"] = cmd.clip_id
    
    if cmd.clip_id == "WEBCAM":
        CURRENT_STATE["video_source"] = "WEBCAM"
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
    now = time.time()
    agent.escalation_log.append({
        "event_id": f"RESOLVE-{int(now * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "breach_type": "RESOLVED_BY_NURSE",
        "action_taken": "Bedside Attended & Bed Tripped Alarms Cleared by Nurse Sarah Jenkins, RN",
        "patient_id": active_patient.patient_id
    })
    engine.active_verdict = "PATIENT_REST_NORMAL"
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
            frame = None
            if CURRENT_STATE["video_source"] == "WEBCAM" and webcam_cap is not None and webcam_cap.isOpened():
                ret, live_f = webcam_cap.read()
                if ret and live_f is not None:
                    frame = live_f
            elif current_cap is not None and current_cap.isOpened():
                ret, video_f = current_cap.read()
                if not ret or video_f is None:
                    # Loop video seamlessly
                    current_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, video_f = current_cap.read()
                if ret and video_f is not None:
                    frame = video_f
                    
            if frame is None:
                frame = np.full((360, 640, 3), 30, dtype=np.uint8)
                cv2.putText(frame, "Awaiting Camera / Video Feed...", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
                
            telemetry = engine.process_frame(frame)
            
            # Agent evaluation
            agent_decision = agent.evaluate(telemetry, active_patient.dict())
            telemetry["agent"] = agent_decision
            telemetry["patient"] = active_patient.dict()
            telemetry["clip_info"] = {
                "active_clip": CURRENT_STATE["clip_id"],
                "source": CURRENT_STATE["video_source"],
                "dataset_citation": "GMDCSA24 Human Fall Dataset (CC BY 4.0)"
            }
            
            await websocket.send_json(telemetry)
            await asyncio.sleep(1.0 / 25.0)
            
    except WebSocketDisconnect:
        pass
