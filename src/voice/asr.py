"""Automatic speech recognition (ASR) wrapper with fallback to text input.

This module attempts to use VOSK (offline) or SpeechRecognition with default microphone. If
microphone or ASR libraries are unavailable, it falls back to reading text from stdin.

Note: For robust production use, configure a reliable ASR provider and microphone setup.
"""

import sys


def listen(prompt: str = None, timeout: int = 30) -> str:
    """Listen for a spoken response and return the transcribed text. If ASR not available,
    prompt for typed input instead.

    The function never raises for missing libraries; it simply falls back to text input.
    """
    if prompt:
        print(prompt)

    # Try VOSK (offline) if installed
    try:
        from vosk import Model, KaldiRecognizer
        import pyaudio
        import json

        # Note: user must have a VOSK model installed under ./models/vosk-model-small
        model_path = "./models/vosk-model-small"
        try:
            model = Model(model_path)
        except Exception:
            print("VOSK model not found at ./models/vosk-model-small; falling back to text input.")
            return input('Type response> ')

        rec = KaldiRecognizer(model, 16000)
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        stream.start_stream()
        print("Listening... speak now (press Ctrl+C to abort)")
        # Read a single chunk - this is a simple approach for demo purposes
        data = stream.read(4096)
        if rec.AcceptWaveform(data):
            res = rec.Result()
            obj = json.loads(res)
            text = obj.get('text', '')
        else:
            text = ''
        stream.stop_stream()
        stream.close()
        pa.terminate()
        if text.strip() == '':
            return input('Heard nothing. Type response> ')
        return text
    except Exception:
        # Try SpeechRecognition with default microphone
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print('Listening (SpeechRecognition)...')
                audio = r.listen(source, timeout=timeout)
            try:
                text = r.recognize_google(audio)
                return text
            except Exception:
                return input('ASR failed. Type response> ')
        except Exception:
            # No ASR available - fallback to text input
            return input('Type response> ')
