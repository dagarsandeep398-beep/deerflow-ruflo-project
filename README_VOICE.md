## Voice confirmation design

This project includes a voice-based confirmation layer that carefully requests your approval before any trade execution.

Key properties:
- Paper-first: trades are executed in paper mode unless live mode is explicitly enabled and approved.
- TTS/ASR: uses pyttsx3 for offline TTS and attempts to use VOSK or SpeechRecognition for offline/online ASR. Falls back to typed input if unavailable.
- Safety gates: hard overrides (kill-switch, daily loss, max allocation) that cannot be bypassed by voice confirmation.

Voice confirmation wording and behavior are implemented in src/voice/dialog_manager.py. See that file for exact prompts, timeouts, and override rules.

To run the voice demo (typed fallback available):

1. Install dependencies in a virtual environment (see requirements.txt).
2. Run:

```bash
python examples/voice_demo.py
```

Notes:
- For real microphone support install pyaudio and a VOSK model or allow SpeechRecognition to use Google Cloud ASR (requires network and Google API keys).
- Audio will be stored locally only if you enable a custom recorder. By default, transcripts are printed and stored in the SQLite store if configured.
