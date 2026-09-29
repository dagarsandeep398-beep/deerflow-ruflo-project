# Hindi-first bilingual support

This update adds bilingual voice support to the trading agent.

Supported default languages:
- Hindi (default)
- English (fallback / secondary)

Key features:
- speech input in Hindi or English
- speech output in the selected language
- command parser understands Hindi confirmations, allocations, and risk commands
- voice prompts include the same safety checks and hard-stop behavior

How to run the demo:

```bash
python examples/voice_demo.py
```

If you want to force a language in code:

```python
from src.voice.dialog_manager import HindiDialogManager

dm = HindiDialogManager(language='hi')
# or: HindiDialogManager(language='en')
```

Notes:
- Offline Hindi ASR requires a VOSK Hindi model.
- If no Hindi ASR model is available, the code falls back to typed input.
- Hindi TTS may rely on the operating system speech engine or print text if unavailable.
