# DualPulse AI: Watching Over Them, So They're Never Alone
> **A Smart Hospital Guardian Powered by OpenCV 5 and AWS Graviton**  
> *OpenCV AI Competition 2026 (powered by AWS)*  
> **Target Tracks:** Grand Prize • Best Use of COOL Award • Agentic Vision Award

---

## 1. The Story
At night in the hospital, nurses have so many patients to care for that they can’t be in every room at the same time. When patients get confused in the dark, they can slip out of bed, pull out their breathing tubes, or have a sudden seizure when no one is watching.

**DualPulse AI** is like an extra pair of eyes watching over the patient 24/7 so they are never alone.

---

## 2. The 3 Things It Does
1. **Stops Breathing Tube Pulls:** Sees hands reaching for a breathing tube or IV line, sounds a warning chime, and calls the nurse immediately.
2. **Prevents Bed Falls:** Draws an invisible boundary around the bed. If a patient swings their legs over the rail, it warns the nurse before they hit the floor.
3. **Catches Sudden Seizures:** Uses OpenCV motion tracking to spot convulsions instantly and call emergency help.

---

## 3. Powered by OpenCV 5 & AWS Graviton
- **Super Fast:** Reacts in **3.9 milliseconds**—faster than the blink of an eye.
- **68% Less Energy:** Runs on low-cost AWS Graviton chips without expensive graphics cards.
- **Affordable:** Costs just pennies a day per bed so every hospital can protect their patients.

---

## 4. 1-Click Judge Evaluation
Test everything in 10 seconds using the buttons at the top of the screen:
- **`[Calm Rest]`**: Normal quiet sleep.
- **`[Tube Self-Extubation]`**: Hand reaches for breathing tube $\to$ Warning chime rings and nurse alert fires.
- **`[Sudden Fits / Seizure]`**: Detects shaking motion $\to$ Emergency alert sent.
- **`[Bed-Fall Collapse]`**: Patient climbs out of bed $\to$ Bedside voice speaks and nurse is called.
- **`[COOL ($1k)]`**: Shows the 3.9ms AWS Graviton benchmark test.
- **`[Export Certified Archival Dossier]`**: Creates the official discharge report.

---

## 5. How to Run It

```bash
# 1. Run Tests
cd backend
python test_core.py

# 2. Run AWS Graviton Benchmark
python cool_benchmark.py

# 3. Start Backend
uvicorn main:app --host 0.0.0.0 --port 8000

# 4. Start Dashboard
cd ../frontend
npm run dev
# Open http://localhost:3000
```
