# utils.py

from gtts import gTTS
import io
import streamlit as st

def tts_audio_bytes(text: str) -> bytes:
    """Return MP3 bytes for text using Google TTS."""
    mp3_fp = io.BytesIO()
    gTTS(text).write_to_fp(mp3_fp)
    return mp3_fp.getvalue()

def play_tts(text: str):
    """Play text-to-speech in Streamlit."""
    audio_bytes = tts_audio_bytes(text)
    st.audio(audio_bytes, format="audio/mp3")
