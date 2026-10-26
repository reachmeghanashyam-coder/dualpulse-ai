# DualPulse AI: Closed-Loop Real-Footage Patient Sentinel
> **Deterministic Kinematic Fall Detection & False-Alarm Suppression for Hospital Safety**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Tracks:** Grand Prize ($5,000) • Best Use of COOL Award ($1,000) • Agentic Vision Award ($1,000)  
> 🌐 **Live Web Application (24/7 Cloud):** [https://dualpulse-ai.onrender.com](https://dualpulse-ai.onrender.com)  
> 🎬 **Live Video Demo:** [Watch on YouTube](https://youtu.be/RA5yW_VH4uI)

---

## 1. The Core Problem: Real Patient Falls vs. Hospital Alarm Fatigue
Unassisted falls in acute and step-down hospital wards account for substantial patient injury, extended lengths of stay, and unbillable clinical complications. Existing optical patient monitors fail in practice due to two fatal flaws:
1. **Missed Low-Contrast Falls:** Ambient night lighting and specular reflections obscure patient silhouettes, preventing reliable detection during unassisted bed-exit attempts.
2. **Severe Alarm Fatigue:** Simple motion-energy triggers alarm whenever a patient adjusts their bedding or turns safely in bed. Overwhelmed nursing staff disable the monitors, leaving patients unprotected.

**DualPulse AI** eliminates both failure modes. Operating on real human bedroom and ward fall footage from the **GMDCSA24 benchmark (CC BY 4.0)**, DualPulse AI combines **Closed-Loop OpenCV 5 Frame Conditioning** (`cv2.inpaint` + `cv2.createCLAHE` + `cv2.bilateralFilter`) with a deterministic **Kinematic Trajectory Gate** that evaluates centroid downward descent velocity, bounding-box aspect ratio expansion, and post-collapse immobility over calibrated temporal windows.

---

## 2. Real-Footage Perception & Action Pipeline

```
[ Real Human Fall Video Stream (Volatile RAM) ]
                   │
                   ▼ 1. PERCEIVE (Perceptual Quality Evaluator)
[ Compute μ_I (Luminance), σ_I (Contrast), ρ_glare (Specular Fraction), Laplacian Focus Variance ]
                   │
                   ▼ 2. CONDITION (Closed-Loop OpenCV Image Enhancement)
   ┌───────────────┴────────────────────────────────────────────────────────┐
   ├─ Specular Glare (ρ > 0.6%): cv2.threshold(230) -> cv2.inpaint(TELEA)   │
   ├─ Low-Light / Shadow (μ < 85): cv2.createCLAHE(2.4) + cv2.bilateralFilter│
   └─ Backtrack Verification: If SNR / quality score drops, revert to raw   │
                   │
                   ▼ 3. TRACK & SEGMENT (OpenCV 5 MOG2 Kinematics)
[ cv2.createBackgroundSubtractorMOG2 + Morphological Open/Close + Contour Bounding Box ]
                   │
                   ▼ 4. DETERMINISTIC KINEMATIC FALL DECISION
   ┌───────────────┴────────────────────────────────────────────────────────┐
   ├─ Centroid Descent ΔY (Standing Fall ≥ 20.0%, Chair Slide ≥ 13.0%)     │
   ├─ Bounding Box Height Loss (ΔH ≥ 20–25%)                                │
   ├─ Post-Impact Aspect Ratio Expansion (W/H > 1.0) & Floor Immobility    │
   └─ Temporal Gate: 3 Consecutive Confirmed Frames (Noise Filter)          │
                   │
                   ▼ 5. CLOSED-LOOP 3-TIER CARE CASCADE
   ┌───────────────┴────────────────────────────────────────────────────────┐
   ├─ Tier 1 (Bedside): In-Room 880Hz Orientation Chime + Reassuring Voice  │
   ├─ Tier 2 (Ward Station): STAT Mobile Pager Dispatch with Drop Telemetry │
   ├─ Nurse Attended: Bedside clearance clears alarm & logs resolution time │
   └─ Tier 3 (Shift Audit): SHA-256 sealed EMR event record (Zero saved MP4)│
```

---

## 3. Real Clinical Scenarios & Interactive Demo Modes

The frontend provides an interactive, consumer-grade HUD demonstrating end-to-end autonomous intervention across real human footage:
1. **`1. Standing Transfer Fall` (Primary Showcase):**  
   Patient is standing and walking across the room. At $t = 2.6\text{s}$, a sudden leg collapse drops the centroid downward by **$20.7\%$** and reduces vertical height by **$30.3\%$**. DualPulse AI confirms the fall across 3 consecutive frames, fires the in-room 880Hz chime and voice prompt, dispatches the nurse console, and displays the glowing **`[Nurse Attended]`** acknowledgment button.
2. **`2. Bedside Chair Fall`:**  
   Patient seated in an armchair loses balance and slides down to the floor at $t = 5.0\text{s}$ ($\Delta Y = 13.2\%$). DualPulse AI catches the gradual descent and post-impact stillness, triggering the acute response cascade.
3. **`Live USB Camera`:**  
   Enables judges and evaluators to test real-time OpenCV motion tracking and false-alarm suppression directly from any connected webcam.

---

## 4. AWS Graviton4 & COOL Optimization Engine

Continuous 25 FPS closed-loop processing across multiple hospital beds demands predictable, low-power ARM64 execution. DualPulse AI is benchmarked on **AWS Graviton4 (`c7g.xlarge`)** using **OpenCV 5 C++ COOL (Arm KleidiCV NEON/SVE2)**:

| Metric | Standard x86 Baseline | AWS Graviton4 + Arm KleidiCV (COOL) | Efficiency Multiplier |
| :--- | :--- | :--- | :--- |
| **Average Frame Latency** | 14.08 ms | **3.93 ms** | **72.1% Latency Reduction** |
| **Single-Core Throughput** | 71.0 FPS / core | **254.5 FPS / core** | **3.58x Throughput Gain** |
| **CPU Utilization Load** | 82.5% | **26.4%** | **68.0% CPU Load Reduction** |
| **Ward Concurrency (4 vCPU)**| 7 Concurrent Beds @ 25 FPS | **28 Concurrent Beds @ 25 FPS** | **4.0x Stream Density** |
| **Bed Economics** | $0.170 / hour (`c6i.xlarge`) | **$0.145 / hour (`c7g.xlarge`)** | **$0.038 / bed / day (3-yr Savings Plan)** |

---

## 5. Privacy & Cryptographic Archival Assurance
- **Ephemeral RAM Processing:** Raw camera video frames are processed in volatile memory and purged within $4\text{ms}$. Zero video is ever saved to persistent disk.
- **SHA-256 EMR Audit Ledger:** Clicking **"View Shift Audit Log"** outputs a cryptographically verified JSON audit record documenting incident timestamps, kinematic descent metrics, and nurse resolution times.

---

## 6. Zero-Dependency Verification & Quickstart

```bash
# 1. Run Automated Unit Test Suite (All 5 tests must pass with exit code 0)
cd backend
python -m unittest test_core.py

# 2. Run Reproducible AWS Graviton4 COOL Benchmark
python cool_benchmark.py

# 3. Launch Backend Daemon (FastAPI + OpenCV 5)
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Launch Next.js Production Build
cd ../frontend
npm run build
npm start
# Open http://localhost:3000
```
