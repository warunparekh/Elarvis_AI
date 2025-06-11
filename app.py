# app.py

import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db import (
    init_db, get_convos, create_convo, rename_convo, delete_convo,
    save_message, load_messages, export_chatlog, get_persona, set_persona
)
from llm import huggingface_chat, safe_execute, extract_code
from utils import play_tts

# ─── Configuration ──────────────────────────────────
st.set_page_config(page_title="Jarvis by Elarvis", layout="wide")
init_db()

DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant; you are Jarvis. "
    "You are witty, friendly, curious, and learn from each conversation. "
    "You can change your mood if asked (serious, fun, sarcastic, helpful). "
    "Your developer is Elarvis. You adapt and remember."
)

JARVIS_MOODS = {
    "Friendly":"You sound warm and friendly.",
    "Serious":"You are serious and direct.",
    "Sarcastic":"You are dry and a little sarcastic.",
    "Motivational":"You try to encourage and motivate.",
    "Funny":"You love to joke and make light fun."
}

MAX_CONTEXT = 22

# ─── Session State Initialization ───────────────────
if "active" not in st.session_state:
    convs = get_convos()
    if not convs:
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)
    else:
        st.session_state.active = convs[0][0]
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.active, MAX_CONTEXT)

# ─── Sidebar: Conversations & Settings ───────────────
with st.sidebar:
    st.title("🤖 JARVIS")
    convs = get_convos()
    if not convs:
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)
        convs = get_convos()
    names = [n for _, n in convs]

    sel = st.selectbox("Conversations", names,
        index=names.index(next(name for cid,name in convs if cid==st.session_state.active))
    )
    st.session_state.active = convs[names.index(sel)][0]

    if st.button("➕ New"):
        new = st.text_input("New name", key="new")
        if new:
            cid = create_convo(new, DEFAULT_PERSONA)
            st.session_state.active = cid
            st.session_state.messages = []
            st.experimental_rerun()

    if st.button("✏️ Rename"):
        rn = st.text_input("Rename to", key="rn")
        if rn:
            rename_convo(st.session_state.active, rn)

    if st.button("🗑️ Delete"):
        delete_convo(st.session_state.active)
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)
        st.session_state.messages = []
        st.experimental_rerun()

    # Mood / Persona
    persona = get_persona(st.session_state.active, DEFAULT_PERSONA)
    mood = st.selectbox("Mood", list(JARVIS_MOODS.keys()))
    newp = st.text_area("Persona", value=persona + " " + JARVIS_MOODS[mood], height=100)
    if st.button("💾 Save Persona"):
        set_persona(st.session_state.active, newp)

    st.markdown("---")
    if st.button("📥 Export Chat"):
        log = export_chatlog(st.session_state.active)
        st.download_button("Download log", log, "chatlog.txt")

# ─── Main Chat Display ───────────────────────────────
st.header("💬 Chat with Jarvis")
for i, (role, msg) in enumerate(st.session_state.messages):
    bgcolor = "#ace" if role == "user" else "#146"
    with stylable_container(
        key=f"msg{i}",
        css_styles=(
            f"background-color:{bgcolor};"
            "padding:12px;"
            "border-radius:12px;"
            "margin-bottom:6px;"
        )
    ):
        speaker = "You" if role=="user" else "Jarvis"
        st.markdown(f"**{speaker}:** {msg}")

# ─── Input Form ──────────────────────────────────────
with st.form(key="input_form", clear_on_submit=True):
    user_input = st.text_input("Your message…")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    # record user
    save_message(st.session_state.active, "user", user_input)
    st.session_state.messages.append(("user", user_input))

    # code vs chat
    code = extract_code(user_input)
    if code:
        result = safe_execute(code)
        save_message(st.session_state.active, "assistant", result)
        st.session_state.messages.append(("assistant", result))
    else:
        with st.spinner("Jarvis is thinking…"):
            reply = huggingface_chat(st.session_state.active, user_input)
        save_message(st.session_state.active, "assistant", reply)
        st.session_state.messages.append(("assistant", reply))

    # play TTS
    play_tts(st.session_state.messages[-1][1])

# Streamlit auto-reruns, no rerun calls needed
