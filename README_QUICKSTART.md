# Phone-first self-hosted AI Trading Agent

This package provides a simple, paper-first trading agent that is designed to be controlled from a phone and run in the background on a small server or local machine.

Features included
- Mobile-friendly web dashboard served from the backend
- Voice/text command endpoint in Hindi and English
- Risk and safety checks before trade proposals are accepted
- Paper-mode execution by default
- Multi-timeframe, global-market analysis hooks
- Audit and status endpoints
- Docker support for easy deployment

Quick start
1. Copy `.env.example` to `.env` and fill in any optional API keys.
2. Run:

```bash
chmod +x scripts/run_all_demo.sh
./scripts/run_all_demo.sh
```

3. Open the app in a browser on your phone or desktop:

```text
http://localhost:8000
```

4. Try a sample command in the text box:

- "Start monitoring EURUSD and NASDAQ in 5m and 1h"
- "Pause trading"
- "Resume trading"

Important safety defaults
- Paper mode is enabled by default.
- Live mode remains disabled until you explicitly turn it on in `.env`.
- Per-trade allocation and daily loss limits are enforced before a proposal is accepted.

Files you may want to review
- `app.py` — FastAPI app with web dashboard and command endpoints
- `docker-compose.yml` — service configuration
- `.env.example` — settings template
- `src/` — analysis, learning, broker integration modules

This is designed to be a safe starting layer before you add a real broker or advanced live execution.
