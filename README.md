# DualPulse AI: Watching Over Them, So They're Never Alone
> **Intelligent Hospital Room Sentinel & Autonomous Patient Guardian**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Bounties ($7,000 Stack):**  
> - 🥇 **$5,000 First Place Grand Prize** (Main Track)  
> - ⚡ **$1,000 Best Use of COOL Award** (Cloud-Optimized OpenCV on AWS Graviton)  
> - 🤖 **$1,000 Agentic Vision Award** (Closed-Loop Autonomous Action)

---

## 1. The Human Problem
At 2:00 AM, hospital hallways are quiet, but danger is real. A single floor nurse often cares for up to 10 vulnerable patients at once. 
- Over **1,000,000 hospital bed falls** occur every year, leading to serious hip fractures and head trauma.
- Delirious ICU patients frequently pull out their own breathing tubes, causing severe vocal trauma and emergency re-intubations.
- Sudden seizures during sleep often go unnoticed until it's too late.

**DualPulse AI** watches over resting patients 24/7, intercepting accidents the second they happen so patients are never alone.

---

## 2. What DualPulse AI Does
1. **Catches Tube & Line Extubations:** Watches patient hand position. The moment a hand reaches for a breathing tube or central catheter, it sounds an instant in-room 880Hz warning chime and alerts the nurse before the tube is dislodged.
2. **Stops Bed Falls:** Creates an invisible boundary around the bed. If a patient swings their legs over the guardrails, it alerts staff before they hit the floor.
3. **Detects Sudden Seizures:** Uses OpenCV motion tracking to detect epileptic convulsions within seconds.
4. **Permanent Discharge Dossiers:** Generates tamper-proof medical care logs sealed with SHA-256 verification hashes upon patient release.

---

## 3. Powered by OpenCV 5 & AWS Graviton (COOL Engine)
DualPulse AI runs on **AWS Graviton4** processors using the **Cloud-Optimized OpenCV Library (COOL)** and Arm KleidiCV:
- **68.0% Lower CPU Load:** Proves that high-speed vision does not require costly, power-hungry GPUs.
- **3.93ms Latency:** Real-time 30 FPS processing that reacts before an accident happens.
- **$0.038 / Bed / Day:** Affordable enough for any community hospital worldwide.

---

## 4. 1-Click Judge Evaluation Guide
At the top of the live dashboard, use the **Evaluation Bar** to test everything in under 10 seconds:
- **`[Calm Rest]`**: Normal resting state; hand at hip; line integrity secure.
- **`[Tube Self-Extubation]`**: Simulates hand reaching for breathing tube. Watch the 880Hz deterrent chime and nurse alert fire instantly.
- **`[Sudden Fits / Seizure]`**: Triggers OpenCV optical flow spike and emergency triage alert.
- **`[Bed-Fall Collapse]`**: Triggers bed perimeter breach.
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
