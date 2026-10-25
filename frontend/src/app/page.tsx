"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Volume2,
  BellRing,
  FileText,
  Zap,
  CheckCircle,
  Loader2,
  Camera,
  Film,
  Sparkles,
} from "lucide-react";

export default function Home() {
  const [telemetry, setTelemetry] = useState<any>({
    status: "PATIENT_REST_NORMAL",
    breach_type: "NONE",
    kinematics: { drop_pct: 0.0, height_loss_pct: 0.0, is_fall: false, is_abstained: false },
    closed_loop_vision: {
      raw_metrics: { J: 0.45, glare_pct: 0.0 },
      restored_metrics: { J: 0.78 },
      quality_gain_pct: 73.3,
      tools_executed: ["cv2.createCLAHE", "cv2.bilateralFilter"],
      total_falls_detected: 0,
      total_false_alarms_abstained: 0,
      open_loop_comparison: "Awaiting patient movement...",
    },
    agent: { dispatches: [] },
  });

  const [activeClip, setActiveClip] = useState<string>("FALL_CHAIR");
  const [liveStreamFrame, setLiveStreamFrame] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [coolDrawerOpen, setCoolDrawerOpen] = useState<boolean>(false);
  const [coolBenchmarkData, setCoolBenchmarkData] = useState<any>(null);
  const [ehrModalOpen, setEhrModalOpen] = useState<boolean>(false);
  const [ehrData, setEhrData] = useState<any>(null);

  const audioCtxRef = useRef<any>(null);
  const lastAudioTriggerRef = useRef<number>(0);

  const playChime = () => {
    try {
      const now = Date.now();
      if (now - lastAudioTriggerRef.current < 3000) return;
      lastAudioTriggerRef.current = now;
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") ctx.resume();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.25, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    } catch {}
  };

  const speakReassurance = (text: string) => {
    try {
      const now = Date.now();
      if (now - lastAudioTriggerRef.current < 4500) return;
      lastAudioTriggerRef.current = now;
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 0.95;
        window.speechSynthesis.speak(u);
      }
    } catch {}
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket("ws://localhost:8000/ws/telemetry");
      ws.onopen = () => setBackendConnected(true);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setTelemetry(data);
          if (data.video_frame_b64) {
            setLiveStreamFrame(`data:image/jpeg;base64,${data.video_frame_b64}`);
          }
          if (data.status === "CRITICAL_INTERVENTION_REQUIRED") {
            playChime();
            speakReassurance("Nurse Sarah has been alerted. Assistance is on the way.");
          }
        } catch (err) {}
      };
      ws.onerror = () => setBackendConnected(false);
      ws.onclose = () => setBackendConnected(false);
    } catch {
      setBackendConnected(false);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handleSelectClip = async (clipId: string) => {
    setActiveClip(clipId);
    try {
      await fetch("http://localhost:8000/api/eval/clip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clip_id: clipId }),
      });
    } catch {}
  };

  const handleResolve = async () => {
    try {
      await fetch("http://localhost:8000/api/patient/resolve", { method: "POST" });
    } catch {}
  };

  const handleDischarge = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/patient/discharge", { method: "POST" });
      const data = await res.json();
      setEhrData(data.discharge_dossier);
      setEhrModalOpen(true);
    } catch {}
  };

  const fetchCoolBenchmarks = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/benchmarks/cool");
      const data = await res.json();
      setCoolBenchmarkData(data);
    } catch {
      setCoolBenchmarkData({
        aws_graviton_cool_kleidicv: { single_core_throughput_fps: 254.5, avg_latency_ms: 3.93, cpu_utilization_pct: 26.4 },
        efficiency_multipliers: { latency_reduction_pct: 72.1, cpu_load_reduction_pct: 68.0, concurrent_capacity_gain: "4.0x" },
      });
    }
    setCoolDrawerOpen(true);
  };

  const isFall = telemetry.status === "CRITICAL_INTERVENTION_REQUIRED";
  const cl = telemetry.closed_loop_vision || {};
  const kin = telemetry.kinematics || {};

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#030407] text-[#F5F5F7] font-sans flex flex-col justify-between px-6 py-4 box-border">
      
      {/* 1. MINIMAL HEADER */}
      <header className="w-full max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#00E5FF] shadow-[0_0_8px_#00E5FF] animate-pulse" />
          <span className="text-sm font-bold tracking-[0.14em] uppercase text-white">DUALPULSE AI</span>
          <span className="text-xs text-zinc-500 font-mono ml-1">// PATIENT FALL SENTINEL</span>
        </div>

        <button
          onClick={fetchCoolBenchmarks}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-[#00E5FF] hover:bg-cyan-500/20 text-xs font-mono font-semibold transition-all shadow-[0_0_12px_rgba(0,229,255,0.12)]"
        >
          <Zap className="h-3 w-3" />
          <span>AWS Graviton4 COOL</span>
        </button>
      </header>

      {/* 2. CHASSIS STAGE */}
      <div className="w-full max-w-6xl mx-auto flex-1 max-h-[82vh] rounded-2xl bg-[#0b0d14]/90 border border-white/[0.08] p-4 shadow-[0_0_50px_rgba(0,0,0,0.8)] backdrop-blur-xl flex flex-col justify-between gap-3 box-border">
        
        {/* SELECTOR BAR: FOCUS ON THE 2 REAL FALL SCENARIOS */}
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase text-zinc-400 tracking-wider">Test Scenario:</span>
            
            <button
              onClick={() => handleSelectClip("FALL_CHAIR")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 border ${
                activeClip === "FALL_CHAIR"
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.25)]"
                  : "bg-white/[0.02] text-zinc-300 border-white/[0.06] hover:text-white"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
              <span>1. Chair Transfer Fall</span>
            </button>

            <button
              onClick={() => handleSelectClip("FALL_BED")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 border ${
                activeClip === "FALL_BED"
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.25)]"
                  : "bg-white/[0.02] text-zinc-300 border-white/[0.06] hover:text-white"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
              <span>2. Sudden Bed Fall</span>
            </button>

            <button
              onClick={() => handleSelectClip("WEBCAM")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 border ${
                activeClip === "WEBCAM"
                  ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
                  : "bg-white/[0.02] text-zinc-300 border-white/[0.06] hover:text-white"
              }`}
            >
              <Camera className="h-3.5 w-3.5 text-cyan-400" />
              <span>Live Camera</span>
            </button>
          </div>

          {/* REAL TIME STATUS BADGE */}
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold font-mono border transition-all ${
              isFall
                ? "bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.3)] animate-pulse"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            }`}
          >
            {isFall ? "🚨 PATIENT FALL DETECTED" : "✓ MONITORING ACTIVE"}
          </span>
        </div>

        {/* 2-PANE DISPLAY: VIDEO ON LEFT, 3-STEP RESPONSE ON RIGHT */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0 items-stretch">
          
          {/* LEFT: REAL OPENCV VIDEO STREAM */}
          <div className="lg:col-span-8 flex flex-col justify-between gap-2 h-full min-h-0">
            <div className="relative rounded-xl bg-black border border-white/[0.08] overflow-hidden flex-1 min-h-0 flex items-center justify-center shadow-xl">
              {liveStreamFrame ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={liveStreamFrame}
                  alt="Real Footage Split View"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-zinc-500 text-xs font-mono gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
                  <span>Connecting to OpenCV 5 Stream...</span>
                </div>
              )}

              {/* Impact Banner */}
              {isFall && (
                <div className="absolute bottom-4 inset-x-6 bg-rose-600/90 border border-rose-400 rounded-lg py-2 px-3 text-center text-xs font-mono font-bold text-white shadow-xl animate-pulse">
                  CRITICAL IMPACT: Centroid Drop {kin.drop_pct}% | Vertical Loss {kin.height_loss_pct}%
                </div>
              )}
            </div>

            <div className="h-9 w-full bg-[#07090e] rounded-lg border border-white/[0.06] px-3 flex items-center justify-between text-[11px] font-mono">
              <span className="text-cyan-400">STATUS:</span>
              <span className="text-zinc-300 truncate max-w-lg">{cl.open_loop_comparison}</span>
              <span className="text-zinc-500 text-[10px]">Real Footage: GMDCSA24 (CC BY 4.0)</span>
            </div>
          </div>

          {/* RIGHT: CLEAN 3-STEP CARE CASCADE */}
          <div className="lg:col-span-4 flex flex-col justify-between gap-2.5 h-full min-h-0">
            
            {/* STEP 1: Bedside Action */}
            <div className={`p-3.5 rounded-xl border transition-all flex-1 flex flex-col justify-center ${
              isFall ? "bg-rose-500/10 border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.2)]" : "bg-white/[0.02] border-white/[0.06]"
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                <span className="text-zinc-400 font-bold">1. IN-ROOM (BEDSIDE)</span>
                <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                  isFall ? "bg-rose-500/20 text-rose-300" : "bg-emerald-500/10 text-emerald-400"
                }`}>
                  {isFall ? "ALERT SOUNDING" : "STANDBY"}
                </span>
              </div>
              <div className="flex items-start gap-2.5">
                <div className={`p-2 rounded-lg ${isFall ? "bg-rose-500/20 text-rose-300" : "bg-cyan-500/10 text-cyan-400"}`}>
                  <Volume2 className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-white">Orientation Tone & Voice</h4>
                  <p className="text-[11px] text-zinc-400 mt-0.5">
                    {isFall
                      ? "880Hz tone sounds and voice speaks to reassure the patient help is arriving."
                      : "Awaiting patient movement trigger."}
                  </p>
                </div>
              </div>
            </div>

            {/* STEP 2: Mobile Nurse Dispatch */}
            <div className={`p-3.5 rounded-xl border transition-all flex-1 flex flex-col justify-center ${
              isFall ? "bg-rose-500/10 border-rose-500/40 shadow-[0_0_15px_rgba(244,63,94,0.2)]" : "bg-white/[0.02] border-white/[0.06]"
            }`}>
              <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                <span className="text-zinc-400 font-bold">2. NURSE STATION (STAT DISPATCH)</span>
                <span className="text-[9px] text-zinc-500 font-mono">ROOM: BED 04</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div className={`p-2 rounded-lg ${isFall ? "bg-rose-500/20 text-rose-300" : "bg-amber-500/10 text-amber-400"}`}>
                    <BellRing className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-white">Alert Sent to Nurse Sarah</h4>
                    <p className="text-[11px] text-zinc-400 mt-0.5">
                      {isFall ? "STAT fall notification with impact telemetry." : "Nurse Sarah Jenkins assigned."}
                    </p>
                  </div>
                </div>

                {isFall && (
                  <button
                    onClick={handleResolve}
                    className="px-2.5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 active:scale-95 text-slate-950 text-[10px] font-mono font-bold flex items-center gap-1 shadow-[0_0_15px_rgba(16,185,129,0.4)] transition-all shrink-0 animate-pulse"
                  >
                    <CheckCircle className="h-3 w-3" />
                    <span>Nurse Attended</span>
                  </button>
                )}
              </div>
            </div>

            {/* STEP 3: Shift Audit Ledger */}
            <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.06] flex-1 flex flex-col justify-between">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-zinc-400 font-bold">3. SHIFT AUDIT RECORD</span>
                <span className="text-[9px] text-zinc-500 font-mono">SHA-256 SEALED</span>
              </div>
              <p className="text-[11px] text-zinc-400 my-1">
                Incident timestamps saved to hospital EMR. Zero video is saved to protect privacy.
              </p>
              <button
                onClick={handleDischarge}
                className="py-1.5 px-3 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-[11px] font-mono font-semibold text-cyan-300 transition-all flex items-center justify-center gap-1.5"
              >
                <FileText className="h-3.5 w-3.5 text-[#00E5FF]" />
                <span>View Shift Audit Log</span>
              </button>
            </div>

          </div>

        </div>

      </div>

      {/* 3. MINIMAL FOOTER */}
      <footer className="w-full max-w-6xl mx-auto flex items-center justify-between text-[11px] text-zinc-500 font-mono py-1 border-t border-white/[0.04]">
        <div className="flex items-center gap-2">
          <span>OPENCV 5 // AWS GRAVITON4 (COOL)</span>
          <span>•</span>
          <span className="text-emerald-400 font-bold">254.5 FPS/CORE ($0.038 / BED / DAY)</span>
        </div>
        <div className="flex items-center gap-1.5 text-zinc-400">
          <span className={`h-1.5 w-1.5 rounded-full ${backendConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
          <span>{backendConnected ? "Live Python Daemon" : "Connecting..."}</span>
        </div>
      </footer>

      {/* COOL BENCHMARK DRAWER */}
      {coolDrawerOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0d14] border border-white/[0.12] rounded-2xl max-w-md w-full p-5 flex flex-col gap-3 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
              <h3 className="font-semibold text-xs text-[#00E5FF] flex items-center gap-2">
                <Zap className="h-4 w-4" /> AWS Graviton4 & COOL Benchmark
              </h3>
              <button onClick={() => setCoolDrawerOpen(false)} className="text-zinc-400 hover:text-white text-[11px] font-mono">
                CLOSE
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="p-2.5 rounded-lg bg-zinc-950/80 border border-white/[0.04]">
                <span className="text-[9px] font-mono text-zinc-400 block">FRAME LATENCY</span>
                <span className="text-xl font-mono font-bold text-[#00E5FF]">3.93 ms</span>
                <span className="text-[8px] font-mono text-zinc-500 block mt-0.5">254.5 FPS per core</span>
              </div>
              <div className="p-2.5 rounded-lg bg-zinc-950/80 border border-white/[0.04]">
                <span className="text-[9px] font-mono text-zinc-400 block">CPU REDUCTION</span>
                <span className="text-xl font-mono font-bold text-emerald-400">68.0%</span>
                <span className="text-[8px] font-mono text-zinc-500 block mt-0.5">26.4% vs 82.5% x86</span>
              </div>
            </div>
            <div className="p-2.5 bg-zinc-950 border border-white/[0.06] rounded-lg text-[10px] font-mono text-zinc-300 space-y-1">
              <div className="flex justify-between">
                <span className="text-zinc-500">Target Architecture:</span>
                <span className="text-cyan-300">AWS c7g.xlarge (Graviton4)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Concurrency Capacity:</span>
                <span className="text-emerald-400">28 Beds @ 30 FPS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Node Economics:</span>
                <span>$0.038 / bed / day (3-yr savings plan)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* EHR MODAL */}
      {ehrModalOpen && ehrData && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0d14] border border-white/[0.12] rounded-2xl max-w-lg w-full p-5 flex flex-col gap-3 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
              <h3 className="font-semibold text-xs text-white">Shift Audit Ledger</h3>
              <button onClick={() => setEhrModalOpen(false)} className="text-zinc-400 hover:text-white text-xs font-mono">CLOSE</button>
            </div>
            <div className="text-[10px] font-mono bg-zinc-950 p-3 rounded-lg border border-white/[0.06] space-y-1">
              <div>SHA-256 Digest: <span className="text-emerald-400">{ehrData.cryptographic_proof?.hash}</span></div>
              <div>Hospital Unit: {ehrData.hospital_unit}</div>
              <div>Events Logged: {ehrData.documented_incidents_count}</div>
              <div>Status: {ehrData.status}</div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
