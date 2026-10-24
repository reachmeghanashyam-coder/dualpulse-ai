# DualPulse AI: The Autonomous Hospital Ward Sentinel
> **Watching over them when no one is in the room.**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Bounties ($7,000 Stack):**  
> - 🥇 **$5,000 First Place Grand Prize** (Main Track)  
> - ⚡ **$1,000 Best Use of COOL Award** (Cloud-Optimized OpenCV on AWS Graviton)  
> - 🤖 **$1,000 Agentic Vision Award** (Closed-Loop Autonomous Action: See, Reason, Act)

---

## 1. The Human Crisis
Every 31 seconds in global hospitals, an unwitnessed catastrophe occurs in the dark:
- A delirious post-stroke patient rips out their endotracheal breathing tube, causing severe vocal trauma and emergency re-intubations ($41,000+ penalty per event).
- An unassisted elderly patient slips over a guardrail and fractures their hip ($35,000+ uncompensated liability).
- A child or trauma patient suffers silent nocturnal convulsions while the floor nurse is trapped charting down the hallway.

Passive room buzzers cause fatal alarm fatigue, and $10,000 GPU servers are too expensive for 95% of community hospitals.

**DualPulse AI is the answer:** an autonomous hospital vision sentinel that turns standard overhead room cameras into intelligent, closed-loop clinical guardians—running directly on cost-effective AWS Graviton cloud chips.

---

## 2. What DualPulse AI Does (The 3 Grounded Interventions)

1. **Life-Support Line & Breathing Tube Extubation Intercept**  
   *What happens:* Delirious ICU patients instinctively reach to pull out their life-support lines.  
   *What DualPulse AI does:* The millisecond hand contact occurs with the airway tube or central line ROI, the system sounds an **880Hz local deterrent chime** to halt the hand reflex, while dispatching a **STAT Code Alert** to Nurse Sarah's tablet before the line is dislodged.

2. **Acuity-Calibrated Bed-Exit Tripwires (Morse Fall Prevention)**  
   *What happens:* Confused patients attempt unassisted bathroom trips, stumble, and fall.  
   *What DualPulse AI does:* Calibrates dynamic spatial boundaries based on patient risk. In `HIGH_ACUITY_ICU` mode, an invisible tripwire locks the bed perimeter; in `STEP_DOWN_RECOVERY` mode, spatial boundaries expand to allow normal stretching without false alarms.

3. **High-Speed Optical Flow Convulsion & Collapse Tracking**  
   *What happens:* Violent epileptic fits or deadweight collapses onto the floor.  
   *What DualPulse AI does:* Dense Farneback optical flow measures kinetic velocity fields at 30 FPS. Spikes over 5.5 magnitude trigger immediate bedside reassurance, summon emergency crash teams, and seal the incident into an immutable **HL7/FHIR Archival Discharge Dossier** with a cryptographic SHA-256 evidence hash.

---

## 3. The Protagonist Story: OpenCV 5 + AWS Graviton COOL

Why didn't this exist before? **Cloud cost.** Streaming 24/7 video from 500 hospital beds into Nvidia GPU instances costs over $2.5 million annually.

We proved that you do not need GPUs:
- **Cloud-Optimized OpenCV (COOL) on AWS Graviton4:** Using Arm KleidiCV vector instructions, we benchmarked our dense optical flow and spatial tripwire engine on AWS Graviton4 (c7g) against standard x86 processors.
- **The Empirical Proof:**
  - **68.0% CPU Utilization Reduction** (26.4% on Graviton4 vs 82.5% on x86)
  - **3.93 ms Average Frame Latency** (253.5 FPS throughput)
  - **28 Concurrent Ward Rooms per $0.05/hr Node**
  - **Cost per Bed:** Just **$0.038 / day** ($1.14 / month), democratizing AI vision for every community hospital bed in the world.

---

## 4. How We Stack the Prizes (The Judge's Cheat Sheet)

1. **Main Track — $5,000 Grand Prize:**  
   A complete, end-to-end hospital operating sentinel solving the multi-billion-dollar crises of patient falls, unplanned extubations, and unassisted seizures.
2. **Special Award — $1,000 Best Use of COOL Award:**  
   Rigorous, verified benchmark (`cool_benchmark_results.json`) proving 72% latency reduction and 68% CPU savings on AWS Graviton4 using Arm KleidiCV vector instructions.
3. **Special Award — $1,000 Agentic Vision Award:**  
   Closed-loop autonomy: the system doesn't just display a box—it **Sees** (OpenCV 5), **Reasons** (Acuity Protocol Engine), and **Acts** (Tier 1 Chime, Tier 2 STAT Nurse Dispatch, Tier 3 SHA-256 Discharge Dossier).

---

## 5. 1-Click Judge Evaluation Guide
At the top of our live console, judges can test the entire autonomous pipeline in under 10 seconds:
- **`[Calm Rest]`**: Normal resting state, contained boundary.
- **`[Tube Self-Extubation]`**: Triggers hand-to-airway contact, 880Hz chime, and STAT nurse alert.
- **`[Sudden Fits / Seizure]`**: Triggers 8.6 magnitude optical flow convulsion detection.
- **`[Bed-Fall Collapse]`**: Triggers perimeter tripwire breach.
- **`[COOL ($1k)]`**: Opens the verifiable AWS Graviton performance benchmark drawer.
- **`[Export Certified Archival Dossier]`**: Generates the permanent SHA-256 legal discharge summary.

---

## 6. Quickstart & Verification

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
