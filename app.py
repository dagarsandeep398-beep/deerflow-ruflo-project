from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Phone-first AI Trading Agent", version="0.1.0")

MODE = os.getenv("AGENT_MODE", "paper")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "hi")
MAX_TRADE_ALLOCATION_PCT = float(os.getenv("MAX_TRADE_ALLOCATION_PCT", "2.0"))
MAX_DAILY_LOSS_PCT = float(os.getenv("MAX_DAILY_LOSS_PCT", "2.0"))
LIVE_MODE_ENABLED = os.getenv("LIVE_MODE_ENABLED", "false").lower() == "true"


@dataclass
class SafetyState:
    live_mode_enabled: bool = LIVE_MODE_ENABLED
    max_trade_allocation_pct: float = MAX_TRADE_ALLOCATION_PCT
    max_daily_loss_pct: float = MAX_DAILY_LOSS_PCT
    kill_switch: bool = False


SAFETY = SafetyState()


class VoiceCommand(BaseModel):
    text: str
    language: Optional[str] = None


class TradeProposal(BaseModel):
    symbol: str
    side: str
    entry: float
    stop_loss: float
    lot_or_pct: float
    reason: str


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(raw: str) -> str:
    return (raw or "").strip().lower()


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "mode": MODE,
        "live_mode_enabled": SAFETY.live_mode_enabled,
        "language": DEFAULT_LANGUAGE,
        "timestamp": _timestamp(),
    }


@app.get("/api/status")
def status() -> Dict[str, Any]:
    return {
        "mode": MODE,
        "live_mode_enabled": SAFETY.live_mode_enabled,
        "kill_switch": SAFETY.kill_switch,
        "max_trade_allocation_pct": SAFETY.max_trade_allocation_pct,
        "max_daily_loss_pct": SAFETY.max_daily_loss_pct,
        "timestamp": _timestamp(),
    }


@app.post("/api/command")
def receive_command(cmd: VoiceCommand) -> Dict[str, Any]:
    text = _normalize_text(cmd.text)
    language = (cmd.language or DEFAULT_LANGUAGE).lower()

    if not text:
        raise HTTPException(status_code=400, detail="Command text is required.")

    if "pause" in text or "रोक" in text:
        SAFETY.kill_switch = True
        return {
            "status": "paused",
            "message": "Trading paused. Emergency stop is active.",
            "language": language,
        }

    if "resume" in text or "फिर" in text or "जारी" in text:
        SAFETY.kill_switch = False
        return {
            "status": "resumed",
            "message": "Trading resumed.",
            "language": language,
        }

    if "status" in text or "स्थिति" in text:
        return status()

    if "start" in text or "शुरू" in text:
        return {
            "status": "started",
            "message": "Monitoring engine started in paper mode.",
            "mode": MODE,
            "language": language,
            "timestamp": _timestamp(),
        }

    if "example" in text:
        return {
            "status": "accepted",
            "message": "Example: Start monitoring EURUSD and NASDAQ in 5m and 1h; ask for a trade proposal; confirm or cancel.",
            "language": language,
            "timestamp": _timestamp(),
        }

    return {
        "status": "queued",
        "message": f"Command received: '{cmd.text}'. The system is queued for analysis in paper mode.",
        "language": language,
        "timestamp": _timestamp(),
    }


@app.post("/api/trade-proposal")
def trade_proposal(proposal: TradeProposal) -> Dict[str, Any]:
    if SAFETY.kill_switch:
        return {
            "status": "blocked",
            "reason": "kill_switch_active",
            "message": "Trade blocked because the kill switch is active.",
            "timestamp": _timestamp(),
        }

    if proposal.lot_or_pct > SAFETY.max_trade_allocation_pct:
        return {
            "status": "blocked",
            "reason": "allocation_exceeds_limit",
            "message": f"Trade blocked because {proposal.lot_or_pct}% exceeds the configured max of {SAFETY.max_trade_allocation_pct}%.",
            "timestamp": _timestamp(),
        }

    if not LIVE_MODE_ENABLED and MODE == "paper":
        return {
            "status": "paper_only",
            "message": "Trade proposal accepted into paper mode only. Live mode remains disabled until explicitly enabled.",
            "proposal": proposal.model_dump(),
            "timestamp": _timestamp(),
        }

    return {
        "status": "authorized",
        "message": "Proposal authorized for execution according to configured safety limits.",
        "proposal": proposal.model_dump(),
        "timestamp": _timestamp(),
    }


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>AI Trading Agent</title>
          <style>
            body { font-family: Arial, sans-serif; background: #0b1020; color: #edf2ff; margin: 0; padding: 16px; }
            .box { background: #151d31; border-radius: 12px; padding: 18px; margin: 10px 0; }
            button { background: #4f46e5; color: white; border: none; border-radius: 8px; padding: 12px 18px; margin: 8px 4px; cursor: pointer; }
            input, textarea { width: 100%; box-sizing: border-box; padding: 10px; border-radius: 8px; border: 1px solid #34415d; background: #0f172a; color: white; }
            .status { color: #a7f3d0; }
            .danger { color: #fca5a5; }
          </style>
        </head>
        <body>
          <h2>AI Trading Agent</h2>
          <div class="box">
            <div><strong>Mode:</strong> <span id="mode">paper</span></div>
            <div><strong>Live Mode:</strong> <span id="liveMode">disabled</span></div>
            <div class="status" id="result">Ready.</div>
          </div>

          <div class="box">
            <textarea id="command" rows="4" placeholder="Voice or text command: Start monitoring EURUSD and NASDAQ in 5m and 1h"></textarea>
            <button onclick="sendCommand()">Send command</button>
            <button onclick="pauseAgent()">Pause</button>
            <button onclick="resumeAgent()">Resume</button>
          </div>

          <div class="box">
            <label>Symbol</label>
            <input id="symbol" value="EURUSD" />
            <label>Side</label>
            <input id="side" value="buy" />
            <label>Entry</label>
            <input id="entry" value="1.0850" />
            <label>Stop Loss</label>
            <input id="stop" value="1.0800" />
            <label>Allocation %</label>
            <input id="pct" value="1.0" />
            <label>Reason</label>
            <input id="reason" value="Momentum breakout on 15m" />
            <button onclick="submitTradeProposal()">Submit proposal</button>
          </div>

          <script>
            async function sendCommand() {
              const text = document.getElementById('command').value;
              const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text, language: 'hi' })
              });
              const data = await res.json();
              document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }

            async function pauseAgent() {
              const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text: 'pause trading', language: 'hi' })
              });
              const data = await res.json();
              document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }

            async function resumeAgent() {
              const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text: 'resume trading', language: 'hi' })
              });
              const data = await res.json();
              document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }

            async function submitTradeProposal() {
              const payload = {
                symbol: document.getElementById('symbol').value,
                side: document.getElementById('side').value,
                entry: Number(document.getElementById('entry').value),
                stop_loss: Number(document.getElementById('stop').value),
                lot_or_pct: Number(document.getElementById('pct').value),
                reason: document.getElementById('reason').value,
              };
              const res = await fetch('/api/trade-proposal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
              });
              const data = await res.json();
              document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            }

            fetch('/api/status')
              .then(r => r.json())
              .then(data => {
                document.getElementById('mode').textContent = data.mode;
                document.getElementById('liveMode').textContent = data.live_mode_enabled ? 'enabled' : 'disabled';
              });
          </script>
        </body>
        </html>
        """
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
