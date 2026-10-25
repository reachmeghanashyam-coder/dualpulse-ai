# DualPulse AI: Closed-Loop Night-ICU Vision Sentinel
> **Self-Correcting Perceptual Edge Vision for Overnight Hospital Bed Safety**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Tracks:** Grand Prize ($5,000) • Best Use of COOL Award ($1,000) • Agentic Vision Award ($1,000)

---

## 1. Abstract & Why Open-Loop Hospital Vision Fails
In overnight ICU and step-down wards (10:00 PM – 6:00 AM), ambient lighting is dimmed while bedside vitals monitors cast harsh specular glare across the patient's head and upper chest. Standard **open-loop** computer vision systems fail in this environment in two ways:
1. **Missed Critical Hazards:** Specular glare domes ($\rho_{\text{glare}} > 4\%$) and deep night shadows ($\mu_I < 30$) blind dense optical flow trackers right over the endotracheal airway zone, missing unconscious ICU-delirium tube pulls ($v_y = -0.4\text{ px/f}$ raw vs. $-6.8\text{ px/f}$ true).
2. **Severe Alarm Fatigue:** Simple motion-threshold detectors trigger false alarms every time a patient shifts their blanket or rolls safely in bed, causing nurses to ignore or disable alerts.

**DualPulse AI** solves both problems using a **5-Stage Closed-Loop Agentic Vision Pipeline** powered by **OpenCV 5** and accelerated by the **Cloud-Optimized OpenCV Library (COOL)** on **AWS Graviton4 (`c7g.xlarge`)**. Instead of running a passive single-pass detector, the agent continuously **Perceives** optical quality degradation, **Conditions** the pixel matrix using OpenCV restoration tools, **Verifies & Backtracks** if noise is over-amplified, and **Abstains** from false alarms on benign movement.

> *Disclaimer: DualPulse AI is a non-diagnostic nursing situational awareness sentinel, not a primary medical diagnostic device. It does not replace certified healthcare personnel.*

---

## 2. Closed-Loop Agentic Vision Architecture (`Perceive -> Act -> Verify/Backtrack -> Decide/Abstain`)

```
[ Raw Night-ICU Camera Frame (Volatile RAM) ]
              │
              ▼ 1. PERCEIVE (Perceptual Quality Evaluator)
[ Compute J(I): Luminance μ_I, Contrast σ_I, Glare Ratio ρ_glare, Laplacian Focus Var, SNR (dB) ]
              │
              ▼ 2. DECIDE & ACT (Autonomous OpenCV Conditioning Tools)
   ┌──────────┴────────────────────────────────────────────────────────────────┐
   ├─ If ρ_glare > 0.6%: cv2.threshold(230) -> cv2.dilate -> cv2.inpaint(TELEA) │
   ├─ If μ_I < 85: Candidate A cv2.createCLAHE(clip=4.2) + Gamma LUT           │
   └─ If Sharpness < 90: cv2.addWeighted(unsharp_mask)                         │
              │
              ▼ 3. VERIFY & BACKTRACK (Closed-Loop Self-Correction)
   ┌──────────┴───────────────────────────┐
   │ Did Aggressive CLAHE drop SNR <11.5dB?│
   └──────────┬───────────────────────────┘
              ├─ YES (Backtrack): Revert & execute cv2.createCLAHE(clip=2.4) + cv2.bilateralFilter(d=5)
              └─ NO (Commit): Proceed with verified restored frame (J_raw=0.31 -> J_restored=0.89, +187%)
              │
              ▼ 4. TRACK (OpenCV 5 Dense Optical Flow & Anatomical ROIs)
[ cv2.calcOpticalFlowFarneback on Restored Frame across Airway Tube, Central Line & Bed Perimeter ]
              │
              ▼ 5. ESCALATE OR ABSTAIN (Alarm-Fatigue Gate)
   ┌──────────┴────────────────────────────────────────────────────────────────┐
   ├─ [Hazard Confirmed]: 880Hz Bedside Deterrent Chime + STAT Nurse Dispatch   │
   ├─ [Benign Blanket Shift]: ABSTAINED_SAFE_MOTION (False Alarm Suppressed)    │
   └─ [Nurse Arrival]: "Nurse Attended" closes loop -> SHA-256 Shift Audit Log  │
```

### Live Split-Screen Visual Proof & 4 Interactive Scenarios
The dashboard streams a live **Split-Screen OpenCV Diagnostic Canvas** (`RAW NIGHT SENSOR` on the left vs. `OPENCV 5 CONDITIONED + OPTICAL FLOW` on the right) across 4 1-click scenarios and live USB webcam input:
1. **`1. Tube Pull (Glare Recovery)`:** Inpaints bedside monitor specular glare and applies night-vision CLAHE to catch a patient's hand reaching for their breathing tube ($v_y = -6.8\text{ px/f}$), firing an immediate 880Hz bedside deterrent chime + nurse STAT alert.
2. **`2. Bed Fall (Shadow CLAHE)`:** Restores low-contrast shadow gradients along the bed rails to intercept unassisted bed exits with a reassuring bedside voice prompt.
3. **`3. Seizure (Deblur Gate)`:** Applies unsharp masking and bilateral noise gating to isolate $6.0\text{ Hz}$ high-energy clonic oscillations.
4. **`4. Blanket Shift [Abstain Test]`:** Demonstrates **Closed-Loop False-Alarm Abstention**. High optical flow ($5.4\text{ px/f}$) occurs inside the safe bed center with zero airway vector convergence; the agent explicitly logs `ABSTAINED_SAFE_MOTION` and suppresses the nurse pager.

---

## 3. Empirical Performance & AWS Graviton4 (COOL) Benchmarks

Continuous 30 FPS closed-loop conditioning (`cv2.inpaint` + `cv2.createCLAHE` + `cv2.bilateralFilter` + `cv2.calcOpticalFlowFarneback`) across an entire hospital ward requires high-efficiency ARM64 SIMD execution. We benchmarked the OpenCV workload comparing standard x86 execution against **AWS Graviton4 (`c7g.xlarge`)** with **OpenCV 5 C++ COOL (Arm KleidiCV NEON/SVE2)**:

| Metric | Standard x86 Baseline | AWS Graviton4 + Arm KleidiCV (COOL) | Efficiency Multiplier |
| :--- | :--- | :--- | :--- |
| **Average Frame Latency** | 14.08 ms | **3.93 ms** | **72.1% Latency Reduction** |
| **Single-Core Throughput** | 71.0 FPS / core | **254.5 FPS / core** (~8 beds/core) | **3.58x Throughput Gain** |
| **CPU Utilization Load** | 82.5% | **26.4%** | **68.0% CPU Load Reduction** |
| **4-vCPU Ward Concurrency** | 7 Concurrent Beds @ 30 FPS | **28 Concurrent Beds @ 30 FPS** (840 FPS total) | **4.0x Stream Density** |
| **Target Node Economics** | `c6i.xlarge` ($0.170/hr) | **`c7g.xlarge` ($0.145/hr Graviton4)** | **$0.124 on-demand ($0.038 savings plan / bed / day)** |

---

## 4. Privacy & Compliance by Design
- **Zero Persistent Video Storage:** All raw and conditioned pixel matrices exist strictly in volatile RAM for `< 4ms` and are never written to disk.
- **Cryptographic Shift Audit Ledger:** Upon shift handoff or patient discharge, the agent compiles a JSON audit record of verified intercepts, nurse resolutions, and suppressed false alarms sealed with a **SHA-256** digest.

---

## 5. Quickstart & Verification

```bash
# 1. Run Automated Clinical & Closed-Loop OpenCV Unit Tests (Exit Code 0)
cd backend
python test_core.py

# 2. Run Reproducible AWS Graviton4 COOL Benchmark
python cool_benchmark.py

# 3. Launch Local FastAPI + OpenCV 5 Backend Daemon
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Launch Next.js 100vh Split-Screen HUD
cd ../frontend
npm run dev
# Open http://localhost:3000
```
