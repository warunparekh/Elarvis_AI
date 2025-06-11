import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db import (
    init_db, get_convos, create_convo, rename_convo, delete_convo,
    save_message, load_messages, export_chatlog, get_persona, set_persona
)
from llm import build_messages, ollama_chat, safe_execute, extract_code
from utils import play_tts

st.set_page_config(page_title="Jarvis by Elarvis", layout="wide")
init_db()

# Defaults
DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant, only Jarvis. "
    "You are witty, friendly, curious, and learn from each conversation. "
    "Your developer is Elarvis."
)
JARVIS_MOODS = {
    "Friendly":"You sound warm and friendly.",
    "Serious":"You are serious and direct.",
    "Sarcastic":"You are dry and a little sarcastic.",
    "Motivational":"You try to encourage and motivate.",
    "Funny":"You love to joke and make light fun."
}
MAX_CONTEXT = 22

# Initialize session state
if "active" not in st.session_state:
    convos = get_convos()
    if not convos:
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)
    else:
        st.session_state.active = convos[0][0]
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.active, MAX_CONTEXT)

# --- Sidebar ---
with st.sidebar:
    st.title("🤖 JARVIS")
    convos = get_convos()
    names = [n for _, n in convos]

    # Conversation selector
    sel = st.selectbox("Conversations", names,
        index=names.index(next(n for i,n in convos if i==st.session_state.active))
    )
    st.session_state.active = convos[names.index(sel)][0]
    if st.button("➕ New"):
        name = st.text_input("New convo name", key="new")
        if name:
            cid = create_convo(name, DEFAULT_PERSONA)
            st.session_state.active = cid
            st.session_state.messages = []
            st.experimental_set_query_params()  # force refresh

    if st.button("✏️ Rename"):
        new = st.text_input("Rename to", key="rn")
        if new:
            rename_convo(st.session_state.active, new)

    if st.button("🗑️ Delete"):
        delete_convo(st.session_state.active)
        st.session_state.active = create_convo("Main", DEFAULT_PERSONA)
        st.session_state.messages = []

    # Mood & persona
    persona = get_persona(st.session_state.active, DEFAULT_PERSONA)
    mood = st.selectbox("Mood", list(JARVIS_MOODS.keys()))
    newp = st.text_area("Persona", value=persona+ " "+JARVIS_MOODS[mood], height=100)
    if st.button("💾 Save Persona"):
        set_persona(st.session_state.active, newp)

    st.markdown("---")
    if st.button("📥 Export Chat"):
        data = export_chatlog(st.session_state.active)
        st.download_button("Download .txt", data, "chatlog.txt")

# --- Main chat area ---
st.header("💬 Chat with Jarvis")
for i,(role,msg) in enumerate(st.session_state.messages):
    bgcolor = "#ace" if role=="user" else "#146"
    with stylable_container(
        key=f"msg{i}",
        css_styles=(
            f"background-color:{bgcolor};"
            "padding:12px;border-radius:12px;margin-bottom:6px;"
        )
    ):
        speaker = "You" if role=="user" else "Jarvis"
        st.markdown(f"**{speaker}:** {msg}")

# --- Input form ---
with st.form(key="input_form", clear_on_submit=True):
    user_input = st.text_input("Your message…")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    # Save user message
    save_message(st.session_state.active, "user", user_input)
    st.session_state.messages.append(("user", user_input))

    # Check for code
    code = extract_code(user_input)
    if code:
        out = safe_execute(code)
        save_message(st.session_state.active, "assistant", out)
        st.session_state.messages.append(("assistant", out))
    else:
        with st.spinner("Jarvis is thinking…"):
            reply = ollama_chat(build_messages(st.session_state.active, user_input))
        save_message(st.session_state.active, "assistant", reply)
        st.session_state.messages.append(("assistant", reply))
    # Play voice
    play_tts(st.session_state.messages[-1][1])

# Refresh displayed messages (Streamlit auto-reruns on form submit)
