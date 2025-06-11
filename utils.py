# utils.py
from gtts import gTTS
import io
import streamlit as st

def tts_audio_bytes(text: str) -> bytes:
    """Generate MP3 bytes for the given text."""
    mp3_fp = io.BytesIO()
    gTTS(text).write_to_fp(mp3_fp)
    return mp3_fp.getvalue()

def play_tts(text: str):
    """Play text-to-speech in the Streamlit app."""
    audio_bytes = tts_audio_bytes(text)
    st.audio(audio_bytes, format="audio/mp3")
