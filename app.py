# app.py

import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db import (
    init_db, get_convos, create_convo, rename_convo, delete_convo,
    save_message, load_messages, export_chatlog, get_persona, set_persona
)
from llm import build_messages, ollama_chat, safe_execute, extract_code
from utils import play_tts

# ─── CONFIG ───────────────────────────────────────────
st.set_page_config(page_title="Jarvis by Elarvis", layout="wide")
init_db()

DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant, only Jarvis. "
    "You are witty, friendly, curious, and learn from each conversation. "
    "You can change your mood if asked (serious, fun, sarcastic, helpful). "
    "Your developer is Elarvis. You keep to-dos, remember preferences, "
    "and adapt your responses over time."
)

JARVIS_MOODS = {
    "Friendly":     "You sound warm and friendly.",
    "Serious":      "You are serious and direct.",
    "Sarcastic":    "You are dry and a little sarcastic.",
    "Motivational": "You try to encourage and motivate.",
    "Funny":        "You love to joke and make light fun."
}

MAX_CONTEXT = 22

# ─── SIDEBAR: Conversations & Settings ─────────────────
st.sidebar.title("🤖 JARVIS")
convos = get_convos()
names  = [name for _, name in convos]

if "active" not in st.session_state:
    if convos:
        st.session_state.active = convos[0][0]
    else:
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)

# Select conversation
selected = st.sidebar.radio("Conversations", names,
    index=names.index(next(n for i,n in convos if i == st.session_state.active))
)
st.session_state.active = convos[names.index(selected)][0]

# Buttons for convos
if st.sidebar.button("➕ New Conversation"):
    new_name = st.sidebar.text_input("Name new convo", key="new")
    if new_name:
        cid = create_convo(new_name, DEFAULT_PERSONA)
        st.session_state.active = cid
        st.experimental_rerun()

if st.sidebar.button("✏️ Rename Conversation"):
    rn = st.sidebar.text_input("New name", key="rn")
    if rn:
        rename_convo(st.session_state.active, rn)
        st.experimental_rerun()

if st.sidebar.button("🗑️ Delete Conversation"):
    delete_convo(st.session_state.active)
    st.experimental_rerun()

# Mood / Persona editing
persona = get_persona(st.session_state.active, DEFAULT_PERSONA)
mood = st.sidebar.selectbox("Jarvis Mood", list(JARVIS_MOODS.keys()))
persona_text = persona + " " + JARVIS_MOODS[mood]
if st.sidebar.button("💾 Save Persona"):
    set_persona(st.session_state.active, persona_text)
    st.experimental_rerun()

st.sidebar.markdown("---")
if st.sidebar.button("📥 Export Chat"):
    log = export_chatlog(st.session_state.active)
    st.sidebar.download_button("Download log as .txt", log, "chatlog.txt")

# ─── MAIN CHAT AREA ────────────────────────────────────
st.header("💬 Chat with Jarvis")
messages = load_messages(st.session_state.active, MAX_CONTEXT)

for idx, (role, msg) in enumerate(messages):
    bgcolor = "#ace" if role == "user" else "#146"
    with stylable_container(
        key=f"msg_{idx}",
        css_styles=(
            f"background-color:{bgcolor};"
            "padding:12px;"
            "border-radius:12px;"
            "margin-bottom:6px;"
        )
    ):
        speaker = "You" if role == "user" else "Jarvis"
        st.markdown(f"**{speaker}:**  {msg}")

# ─── USER INPUT & ACTIONS ───────────────────────────────
prompt = st.text_input("Your message…", key="prompt_input")
send   = st.button("Send")

if send and prompt.strip():
    save_message(st.session_state.active, "user", prompt)
    code = extract_code(prompt)
    if code:
        out = safe_execute(code)
        save_message(st.session_state.active, "assistant", out)
    else:
        with st.spinner("Jarvis is thinking…"):
            reply = ollama_chat(build_messages(st.session_state.active, prompt))
        save_message(st.session_state.active, "assistant", reply)
    st.experimental_rerun()

# ─── PLAY VOICE REPLY ───────────────────────────────────
# After rerun, load latest assistant message and play TTS
messages = load_messages(st.session_state.active, MAX_CONTEXT)
if messages and messages[-1][0] == "assistant":
    play_tts(messages[-1][1])
