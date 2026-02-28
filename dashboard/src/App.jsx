import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = "http://localhost:5000";
const MAX_COUNTDOWN = 30;

const STATUS_CONFIG = {
  CLEAR:     { color: "#30d158", label: "All Clear",     sub: "Patient status normal",        bracket: "#30d158" },
  ALERT:     { color: "#ff9f0a", label: "Monitoring",    sub: "Unusual movement detected",    bracket: "#ff9f0a" },
  COUNTDOWN: { color: "#ff453a", label: "Fall Detected", sub: "Press R to cancel",            bracket: "#ff453a" },
  STOOD_UP:  { color: "#ff9f0a", label: "Stood Up",      sub: "Press R if you are okay",      bracket: "#ff9f0a" },
  FALL:      { color: "#ff453a", label: "Fall Detected", sub: "Immediate attention required", bracket: "#ff453a" },
  EMERGENCY: { color: "#ff453a", label: "Emergency",     sub: "Escalating now",               bracket: "#ff453a" },
};

function Corner({ pos, color }) {
  const size = 52;
  const thickness = 5;
  const offset = 20;
  const style = {
    position: "absolute",
    width: size, height: size,
    ...(pos.includes("top")    ? { top: offset }    : { bottom: offset }),
    ...(pos.includes("left")   ? { left: offset }   : { right: offset }),
  };
  const h = {
    position: "absolute",
    width: size, height: thickness,
    background: color,
    borderRadius: 3,
    boxShadow: `0 0 10px ${color}88`,
    ...(pos.includes("top")    ? { top: 0 }    : { bottom: 0 }),
    ...(pos.includes("left")   ? { left: 0 }   : { right: 0 }),
  };
  const v = {
    position: "absolute",
    width: thickness, height: size,
    background: color,
    borderRadius: 3,
    boxShadow: `0 0 10px ${color}88`,
    ...(pos.includes("top")    ? { top: 0 }    : { bottom: 0 }),
    ...(pos.includes("left")   ? { left: 0 }   : { right: 0 }),
  };
  return (
    <div style={{ ...style, transition: "all 0.4s ease" }}>
      <div style={h}/>
      <div style={v}/>
    </div>
  );
}

export default function App() {
  const [status, setStatus] = useState("CLEAR");
  const [alertLog, setAlertLog] = useState([]);
  const [frame, setFrame] = useState(null);
  const [connected, setConnected] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [showLog, setShowLog] = useState(false);
  const [nosePos, setNosePos] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const socket = io(SOCKET_URL, { transports: ["websocket"] });
    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));
    socket.on("status_update", (d) => { setStatus(d.status); setAlertLog(d.alert_log || []); });
    socket.on("frame", (d) => setFrame(`data:image/jpeg;base64,${d.image}`));
    socket.on("countdown", (d) => setCountdown(d.seconds));
    socket.on("keypoint", (d) => setNosePos(d));
    return () => socket.disconnect();
  }, []);

  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.CLEAR;
  const showCountdown = countdown !== null && countdown > 0 && (status === "COUNTDOWN" || status === "STOOD_UP");
  const isUrgent = showCountdown && countdown <= 10;
  const fallCount = alertLog.filter(e => e.type === "fall").length;

  // Convert nose percentage position to pixel position for the floating tag
  const tagStyle = (() => {
    if (!nosePos || !containerRef.current) {
      // Default: bottom left
      return { position: "absolute", bottom: showCountdown ? 120 : 72, left: 64, transition: "all 0.1s linear" };
    }
    const { width, height } = containerRef.current.getBoundingClientRect();
    const px = nosePos.x * width;
    const py = nosePos.y * height;
    // Place tag to the right of the nose, offset upward slightly
    let left = px + 30;
    let top = py - 20;
    // Clamp so it doesn't go off screen
    left = Math.min(left, width - 220);
    top = Math.max(top, 60);
    top = Math.min(top, height - 100);
    return { position: "absolute", left, top, transition: "all 0.1s linear" };
  })();

  return (
    <div ref={containerRef} style={{
      width: "100vw", height: "100vh",
      background: "#000",
      overflow: "hidden",
      position: "relative",
      fontFamily: "-apple-system, 'SF Pro Display', 'Helvetica Neue', sans-serif",
    }}>

      {/* FULL SCREEN CAMERA */}
      {frame ? (
        <img src={frame} alt="feed" style={{
          position: "absolute", inset: 0,
          width: "100%", height: "100%",
          objectFit: "cover",
        }}/>
      ) : (
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          color: "#444", gap: 12,
        }}>
          <div style={{ fontSize: 48 }}>📷</div>
          <div style={{ fontSize: 13, letterSpacing: "0.08em" }}>Awaiting camera feed...</div>
        </div>
      )}

      {/* VIGNETTE */}
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,0.6) 100%)",
        pointerEvents: "none",
      }}/>

      {/* CORNER BRACKETS */}
      {["top-left","top-right","bottom-left","bottom-right"].map(pos => (
        <Corner key={pos} pos={pos} color={cfg.bracket}/>
      ))}

      {/* TOP LEFT — logo */}
      <div style={{
        position: "absolute", top: 22, left: 80,
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{
          width: 28, height: 28, borderRadius: 7,
          background: "rgba(255,255,255,0.12)", backdropFilter: "blur(10px)",
          border: "1px solid rgba(255,255,255,0.2)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 12, fontWeight: 700, color: "#fff",
        }}>G</div>
        <span style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.9)" }}>GuardianEye</span>
        <div style={{
          display: "flex", alignItems: "center", gap: 5,
          padding: "2px 8px", borderRadius: 20,
          background: "rgba(0,0,0,0.35)", backdropFilter: "blur(8px)",
          border: `1px solid ${connected ? "rgba(48,209,88,0.4)" : "rgba(255,69,58,0.4)"}`,
        }}>
          <div style={{ width: 5, height: 5, borderRadius: "50%", background: connected ? "#30d158" : "#ff453a" }}/>
          <span style={{ fontSize: 10, fontWeight: 600, color: connected ? "#30d158" : "#ff453a" }}>
            {connected ? "Live" : "Off"}
          </span>
        </div>
      </div>

      {/* TOP RIGHT */}
      <div style={{
        position: "absolute", top: 22, right: 80,
        display: "flex", alignItems: "center", gap: 10,
      }}>
        {fallCount > 0 && (
          <div style={{
            padding: "4px 12px", borderRadius: 20,
            background: "rgba(255,69,58,0.25)", backdropFilter: "blur(8px)",
            border: "1px solid rgba(255,69,58,0.4)",
            fontSize: 12, fontWeight: 600, color: "#ff6b6b",
          }}>
            {fallCount} fall{fallCount !== 1 ? "s" : ""} today
          </div>
        )}
        <button onClick={() => setShowLog(v => !v)} style={{
          padding: "5px 14px", borderRadius: 20, cursor: "pointer",
          background: "rgba(255,255,255,0.12)", backdropFilter: "blur(8px)",
          border: "1px solid rgba(255,255,255,0.2)",
          fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.9)",
        }}>
          {showLog ? "Hide Log" : "Event Log"}
        </button>
      </div>

      {/* FLOATING STATUS TAG — follows person's nose */}
      <div style={tagStyle}>
        <div style={{
          display: "inline-flex", alignItems: "center", gap: 10,
          padding: "10px 16px", borderRadius: 14,
          background: "rgba(0,0,0,0.55)", backdropFilter: "blur(16px)",
          border: `1.5px solid ${cfg.color}55`,
          boxShadow: `0 0 24px ${cfg.color}25`,
        }}>
          <div style={{
            width: 9, height: 9, borderRadius: "50%",
            background: cfg.color,
            boxShadow: `0 0 10px ${cfg.color}`,
            flexShrink: 0,
            animation: (status === "FALL" || status === "COUNTDOWN" || status === "EMERGENCY") ? "pulseDot 1s infinite" : "none",
          }}/>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", whiteSpace: "nowrap" }}>
              {cfg.label}
            </div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.55)", marginTop: 1, whiteSpace: "nowrap" }}>
              {cfg.sub}
            </div>
          </div>
        </div>
      </div>

      {/* COUNTDOWN BAR */}
      {showCountdown && (
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          padding: "14px 80px 24px",
          background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: isUrgent ? "#ff6b6b" : "rgba(255,255,255,0.8)", letterSpacing: "0.02em" }}>
              {status === "STOOD_UP" ? "Press R on keyboard if you are okay — emergency in" : "Calling emergency services in"}
            </span>
            <span style={{
              fontSize: 28, fontWeight: 800,
              color: isUrgent ? "#ff453a" : "#ff9f0a",
              fontVariantNumeric: "tabular-nums",
              animation: isUrgent ? "pulseDot 0.5s infinite" : "none",
            }}>
              {Math.ceil(countdown)}s
            </span>
          </div>
          <div style={{ height: 5, background: "rgba(255,255,255,0.15)", borderRadius: 3, overflow: "hidden" }}>
            <div style={{
              height: "100%", borderRadius: 3,
              width: `${Math.min(100, (countdown / MAX_COUNTDOWN) * 100)}%`,
              background: isUrgent
                ? "linear-gradient(to right, #ff453a, #ff6b6b)"
                : "linear-gradient(to right, #ff9f0a, #ffd60a)",
              transition: "width 0.3s linear",
            }}/>
          </div>
        </div>
      )}

      {/* EVENT LOG PANEL */}
      {showLog && (
        <div style={{
          position: "absolute", top: 0, right: 0, bottom: 0,
          width: 280,
          background: "rgba(10,10,10,0.78)", backdropFilter: "blur(20px)",
          borderLeft: "1px solid rgba(255,255,255,0.08)",
          display: "flex", flexDirection: "column",
          padding: "70px 0 20px",
        }}>
          <div style={{ padding: "0 20px 12px", fontSize: 11, fontWeight: 600, color: "rgba(255,255,255,0.35)", letterSpacing: "0.1em", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            EVENT LOG
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "10px 14px" }}>
            {alertLog.length === 0 ? (
              <div style={{ textAlign: "center", color: "rgba(255,255,255,0.2)", fontSize: 12, marginTop: 24 }}>No events yet</div>
            ) : alertLog.map((e, i) => (
              <div key={i} style={{
                padding: "8px 10px", marginBottom: 4, borderRadius: 8,
                background: e.type === "fall" ? "rgba(255,69,58,0.12)" : "rgba(48,209,88,0.08)",
                border: `1px solid ${e.type === "fall" ? "rgba(255,69,58,0.25)" : "rgba(48,209,88,0.2)"}`,
                display: "flex", justifyContent: "space-between", alignItems: "center",
              }}>
                <span style={{ fontSize: 12, color: e.type === "fall" ? "#ff6b6b" : "#30d158" }}>{e.message}</span>
                <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginLeft: 8 }}>{e.time}</span>
              </div>
            ))}
          </div>
          <div style={{ padding: "10px 20px 0", fontSize: 10, color: "rgba(255,255,255,0.18)", lineHeight: 1.5 }}>
            IrvineHacks 2026 · GuardianEye
          </div>
        </div>
      )}

      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000; overflow: hidden; }
        @keyframes pulseDot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.55; transform: scale(0.9); }
        }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 2px; }
      `}</style>
    </div>
  );
}