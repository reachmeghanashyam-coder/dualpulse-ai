import unittest
import numpy as np
import cv2
import os
import sys

sys.path.append(os.path.dirname(__file__))
from real_vision_engine import RealFootageVisionEngine, condition_frame, evaluate_quality
from agent_core import ArchivalHospitalAgent

class TestDualPulseSentinel(unittest.TestCase):
    def setUp(self):
        self.engine = RealFootageVisionEngine(fps=25.0)
        self.agent = ArchivalHospitalAgent(room_id="WARD_BED_04")
        self.backend_dir = os.path.dirname(__file__)

    def test_image_quality_evaluator(self):
        """Perception: Evaluates luminance, contrast, glare fraction, Laplacian focus variance."""
        dark_frame = np.full((360, 640), 20, dtype=np.uint8)
        q = evaluate_quality(dark_frame)
        self.assertIn("mu", q)
        self.assertIn("sigma", q)
        self.assertIn("glare_pct", q)
        self.assertIn("sharpness", q)
        self.assertIn("J", q)
        self.assertLess(q["mu"], 30.0)

    def test_closed_loop_conditioning(self):
        """Conditioning: Tests glare inpainting and CLAHE contrast restoration."""
        img = np.full((360, 640), 35, dtype=np.uint8)
        # Inject synthetic specular monitor glare spot
        cv2.circle(img, (320, 180), 40, 255, -1)
        cond, trace = condition_frame(img)
        self.assertIn("tools_executed", trace)
        self.assertIn("quality_gain_pct", trace)
        self.assertEqual(cond.shape, (360, 640))
        # Glare tool was selected
        self.assertTrue(any("inpaint" in t for t in trace["tools_executed"]))

    def test_standing_fall_clip_verification(self):
        """End-to-End: Verifies standing transfer fall on real GMDCSA24 footage."""
        clip_path = os.path.join(self.backend_dir, "sample_walking_fall.mp4")
        self.assertTrue(os.path.exists(clip_path), f"Clip missing: {clip_path}")
        
        cap = cv2.VideoCapture(clip_path)
        self.assertTrue(cap.isOpened(), "Could not open standing fall clip")
        
        triggered = False
        frame_idx = 0
        trigger_frame = None
        while cap.isOpened() and frame_idx < 120:
            ret, frame = cap.read()
            if not ret:
                break
            res = self.engine.process_frame(frame)
            if res["status"] == "CRITICAL_INTERVENTION_REQUIRED":
                triggered = True
                trigger_frame = frame_idx
                break
            frame_idx += 1
        cap.release()
        
        self.assertTrue(triggered, "Standing transfer fall failed to trigger alarm")
        # Ensure trigger occurs right during collapse (frame 63-75, ~2.5-3.0s)
        self.assertGreaterEqual(trigger_frame, 60, f"Triggered too early at frame {trigger_frame}")
        self.assertLessEqual(trigger_frame, 80, f"Triggered too late at frame {trigger_frame}")

    def test_chair_fall_clip_verification(self):
        """End-to-End: Verifies bedside chair collapse on real GMDCSA24 footage."""
        clip_path = os.path.join(self.backend_dir, "sample_fall.mp4")
        self.assertTrue(os.path.exists(clip_path), f"Clip missing: {clip_path}")
        
        cap = cv2.VideoCapture(clip_path)
        self.assertTrue(cap.isOpened(), "Could not open chair fall clip")
        
        engine = RealFootageVisionEngine(fps=25.0)
        triggered = False
        frame_idx = 0
        while cap.isOpened() and frame_idx < 160:
            ret, frame = cap.read()
            if not ret:
                break
            res = engine.process_frame(frame)
            if res["status"] == "CRITICAL_INTERVENTION_REQUIRED":
                triggered = True
                break
            frame_idx += 1
        cap.release()
        
        self.assertTrue(triggered, "Chair collapse failed to trigger alarm")

    def test_nurse_resolution_and_audit_dossier(self):
        """Action & Archival: Simulates nurse resolution and cryptographic EMR discharge digest."""
        patient = {"patient_id": "PT-8821", "name": "Robert Davis"}
        dummy_telemetry = {"breach_type": "BED_FALL_COLLAPSE", "closed_loop_vision": {"tools_executed": ["cv2.createCLAHE"]}}
        
        # Trigger agent evaluation
        decision = self.agent.evaluate(dummy_telemetry, patient)
        self.assertIn("dispatches", decision)
        self.assertGreater(len(decision["dispatches"]), 0)
        
        # Compile discharge dossier
        dossier = self.agent.compile_archival_discharge_dossier(patient, dummy_telemetry)
        self.assertIn("cryptographic_proof", dossier)
        proof = dossier["cryptographic_proof"]
        self.assertEqual(proof["algorithm"], "SHA-256")
        self.assertTrue(proof["hash"].startswith("sha256:"))
        self.assertEqual(len(proof["hash"]), 71)  # 'sha256:' + 64 hex chars
        self.assertEqual(dossier["patient_clinical_summary"]["id"], "PT-8821")

if __name__ == "__main__":
    unittest.main()
