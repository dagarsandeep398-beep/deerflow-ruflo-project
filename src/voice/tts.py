"""Text-to-speech wrapper with offline fallback.

Uses pyttsx3 if available (offline). Falls back to printing the text when TTS is not available.
"""

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty('rate', 150)
except Exception:
    _tts_engine = None


def speak(text: str):
    """Speak the given text or print it if no TTS engine is available."""
    if _tts_engine is not None:
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception:
            print(f"[TTS] {text}")
    else:
        print(f"[TTS] {text}")
