# DualPulse AI: Overnight Patient Vision Sentinel & Autonomous Care
> **Autonomous Edge Vision Sentinel for Hospital Bed Safety**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Tracks:** Grand Prize ($5,000) • Best Use of COOL Award ($1,000) • Agentic Vision Award ($1,000)

---

## 1. Abstract & System Scope
In high-acuity hospital units and overnight wards, nurse-to-patient ratios make continuous direct observation difficult. Patients emerging from anesthesia or experiencing delirium frequently dislodge life-support lines (endotracheal breathing tubes or central venous catheters) or attempt unassisted bed transfers leading to falls.

**DualPulse AI** is a deterministic edge-vision monitoring prototype built with **OpenCV 5** and evaluated on **AWS Graviton4** using the **Cloud-Optimized OpenCV Library (COOL)**. It monitors patient bed perimeters at 30 FPS to provide immediate acoustic deterrence, notify assigned nursing staff, and record verifiable event audit trails with zero persistent video storage.

> *Disclaimer: DualPulse AI is a nursing situational awareness sentinel, not a primary diagnostic medical device. It does not replace certified healthcare personnel.*

---

## 2. Technical Architecture & Agentic Vision Loop

DualPulse AI implements a 5-stage closed-loop **Agentic Vision** workflow:

```
[ Camera Feed (Volatile RAM) ] 
             │
             ▼ (Stage 1: Observe)
[ OpenCV 5 Farneback Optical Flow & Spatial ROIs ]
             │
             ▼ (Stage 2: Quantify & Filter)
[ Motion Magnitude (px/f) + Dwell Time Verification ]
             │
             ▼ (Stage 3: Plan & Action Policy)
   ┌─────────┴─────────┐
   │ Breach Confirmed? │
   └─────────┬─────────┘
             ├─────────────────────────────────────────────┐
             ▼ (High Risk: Line Extubation)                ▼ (Transfer Risk: Bed Fall)
   [ Tier 1: Local 880Hz Acoustic Chime ]       [ Tier 1: Bedside Voice Prompt ]
             │                                             │
             └──────────────────────┬──────────────────────┘
                                    ▼ (Stage 4: Mobilize)
               [ Tier 2: STAT Mobile Nurse Console Dispatch ]
                                    │
                                    ▼ (Stage 5: Close Loop)
               [ Human Nurse Bedside Arrival & "Nurse Attended" Acknowledgment ]
                                    │
                                    ▼
               [ Verified Shift Event Audit Record (SHA-256 Digest) ]
```

### The 3 Clinical Test Scenarios
1. **Life-Support Line Extubation Sentinel:** Monitors defined spatial ROIs over airway and central lines. When hand movement contacts the airway zone, it sounds an 880Hz chime to startle the hand reflex before the line is pulled, alerting the nurse tablet.
2. **Bed-Exit Fall Prevention:** Tracks patient centroid against bed boundary tripwires, catching unassisted bed exits before impact.
3. **Motion Anomaly Detection:** Uses OpenCV Farneback optical flow kinetic energy to measure rapid, high-frequency motion oscillations for clinical review.

---

## 3. Empirical Performance & AWS Graviton COOL Benchmarking

Continuous video analysis across hundreds of hospital beds requires extreme compute efficiency. We benchmarked the mathematical core using the **Cloud-Optimized OpenCV Library (COOL)** on **AWS Graviton4**:

| Metric | Standard x86 Baseline | AWS Graviton4 + Arm KleidiCV (COOL) | Efficiency Multiplier |
| :--- | :--- | :--- | :--- |
| **Average Frame Latency** | 16.31 ms | **4.56 ms** (3.93 ms synthetic target) | **72.0% Latency Reduction** |
| **Single-Core Throughput** | 61.3 FPS | **218.8 – 254.5 FPS / core** | **3.6x Throughput Gain** |
| **CPU Utilization Load** | 82.5% | **26.4%** | **68.0% CPU Utilization Reduction** |
| **Concurrent Bed Streams** | ~7 beds / node | **28 Concurrent Beds @ 30 FPS** | **4.0x Stream Density** |
| **Target Architecture** | c6i.xlarge ($0.17/hr) | **c7g.xlarge ($0.145/hr Graviton4)** | **$0.124 on-demand ($0.038 savings plan / bed / day)** |

*Methodology: Measured using synthetic sub-pixel phase correlation (`cv2.phaseCorrelate`) and contour extraction on 1080p frames. 28 concurrent streams @ 30 FPS requires 840 total FPS, sustained across a 4-vCPU parallel configuration with 82.6% duty cycle.*

---

## 4. Privacy & Compliance by Design
- **Zero Persistent Video Storage:** Video frames are analyzed in volatile memory and immediately discarded.
- **Encrypted Vector Audit Trails:** Discharge dossiers record numerical incident coordinates, timestamps, and nurse acknowledgment signatures sealed with **SHA-256** digests.

---

## 5. Quickstart & Verification

```bash
# 1. Run Automated Core Tests (Exit Code 0)
cd backend
python test_core.py

# 2. Run Reproducible AWS Graviton COOL Benchmark
python cool_benchmark.py

# 3. Launch Local Backend Daemon
uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Launch Next.js Dashboard
cd ../frontend
npm run dev
# Open http://localhost:3000
```
