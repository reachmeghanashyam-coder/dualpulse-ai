import cv2
import numpy as np
import sys
import os

sys.path.append(r"C:\Users\ghanashyam\.gemini\antigravity\scratch\vitazero-ai\backend")
from real_vision_engine import RealFootageVisionEngine

def evaluate_video(filepath, name):
    engine = RealFootageVisionEngine(fps=25.0)
    cap = cv2.VideoCapture(filepath)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    triggers = []
    abstains = []
    
    for idx in range(total_frames):
        ret, frame = cap.read()
        if not ret: break
        res = engine.process_frame(frame)
        st = res["status"]
        if st == "CRITICAL_INTERVENTION_REQUIRED":
            triggers.append((idx, round(idx/25.0, 2), res["kinematics"]))
        elif st == "ABSTAINED_SAFE_MOTION":
            abstains.append((idx, round(idx/25.0, 2)))
            
    print(f"\n==========================================")
    print(f"VIDEO: {name} (Frames: {total_frames}, {total_frames/25.0:.1f}s)")
    print(f"Total Critical Fall Alerts: {len(triggers)}")
    if triggers:
        first = triggers[0]
        print(f"FIRST FALL ALERT at Frame {first[0]} (t={first[1]}s):")
        print(f"  drop={first[2]['drop_pct']}%, h_loss={first[2]['height_loss_pct']}%")
    print(f"Total Safe Abstentions: {len(abstains)}")

backend_dir = r"C:\Users\ghanashyam\.gemini\antigravity\scratch\vitazero-ai\backend"
evaluate_video(os.path.join(backend_dir, "sample_fall.mp4"), "1. Chair Fall (sample_fall.mp4)")
evaluate_video(os.path.join(backend_dir, "sample_walking_fall.mp4"), "2. Standing Fall (sample_walking_fall.mp4)")
evaluate_video(os.path.join(backend_dir, "sample_adl.mp4"), "3. Normal Safe Motion (sample_adl.mp4)")
