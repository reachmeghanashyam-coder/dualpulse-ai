# DualPulse AI: Watching Over Them, So They're Never Alone
> **Hospital Room Vision Sentinel & Autonomous Care System**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Tracks:** Grand Prize ($5,000) • Best Use of COOL Award ($1,000) • Agentic Vision Award ($1,000)

---

## 1. Overview
In hospital wards at night, nurses have to monitor multiple patients at once. If a patient becomes disoriented and reaches for a life-support line, or attempts an unassisted bed exit, accidents can occur before staff can reach the bedside.

**DualPulse AI** is an intelligent hospital vision system built with OpenCV 5 and AWS Graviton that monitors the patient bed 24/7 to catch critical emergencies the moment they happen.

---

## 2. The 3 Clinical Scenarios
1. **Tube & Line Extubation Intercept:** Tracks hand position relative to breathing tubes and central lines. Contact triggers an immediate in-room 880Hz warning chime to break the hand reflex and alerts the nurse station.
2. **Bed-Exit Fall Prevention:** Sets dynamic perimeter boundaries around the bed. If a high-fall-risk patient swings their legs over the rail, it alerts staff before a floor impact occurs.
3. **Seizure & Convulsion Detection:** Uses OpenCV Farneback optical flow to measure rapid motion spikes, immediately notifying medical teams during epileptic events.

---

## 3. Powered by OpenCV 5 & AWS Graviton (COOL Engine)
Running continuous computer vision across hospital beds can be expensive on GPUs. DualPulse AI was benchmarked on **AWS Graviton4** using the **Cloud-Optimized OpenCV Library (COOL)** with Arm KleidiCV:
- **68.0% CPU Utilization Reduction** compared to standard x86 baseline.
- **3.93 ms Average Frame Latency** (253.5 FPS throughput).
- **Sub-$0.04 / Bed / Day** operational efficiency, making 24/7 room monitoring practical for hospitals worldwide.

---

## 4. 1-Click Judge Evaluation Guide
At the top of the live dashboard, judges can test the full pipeline in under 10 seconds:
- **`[Calm Rest]`**: Normal resting state; line integrity secure.
- **`[Tube Self-Extubation]`**: Hand contacts breathing tube $\to$ 880Hz deterrent chime rings and nurse alert fires.
- **`[Sudden Fits / Seizure]`**: Farneback optical flow detects kinetic spike $\to$ Emergency alert sent.
- **`[Bed-Fall Collapse]`**: Patient breaches bed boundary $\to$ Reassuring bedside voice speaks and nurse is dispatched.
- **`[COOL ($1k)]`**: Opens the verifiable AWS Graviton performance benchmark drawer.
- **`[Export Certified Archival Dossier]`**: Generates the SHA-256 legal discharge summary.

---

## 5. Quickstart & Verification

```bash
# 1. Run Automated Test Suite (Exit Code 0)
cd backend
python test_core.py

# 2. Run Graviton COOL Benchmark
python cool_benchmark.py

# 3. Launch Backend Server
uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Launch Next.js Dashboard
cd ../frontend
npm run dev
# Open http://localhost:3000
```
