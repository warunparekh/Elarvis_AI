# HF_TOKEN   = "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"

# llm.py

import os, sys, io, re, requests
from db import load_messages, get_persona

# ─── Configuration ────────────────────────────────
MODEL_ID = "microsoft/DialoGPT-medium"
API_URL  = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HF_TOKEN = "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"  # optional; DialoGPT is public
HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant, only Jarvis. "
    "Developer is Elarvis. Be witty and friendly."
)

def build_prompt(convo_id, user_prompt):
    persona = get_persona(convo_id, DEFAULT_PERSONA)
    history = load_messages(convo_id)
    # DialoGPT prefers just the last exchange, but we can concatenate
    prompt = persona + "\n"
    for role, content in history[-3:]:
        speaker = "User" if role == "user" else "Jarvis"
        prompt += f"{speaker}: {content}\n"
    prompt += f"User: {user_prompt}\nJarvis:"
    return prompt

def huggingface_chat(convo_id, user_prompt):
    prompt = build_prompt(convo_id, user_prompt)
    payload = {"inputs": prompt}
    try:
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # e.g. {"generated_text":"..."}
        text = data.get("generated_text", "")
        # strip repeat of prompt
        if text.startswith(prompt):
            return text[len(prompt):].strip()
        return text.strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "[Model error: model not found]"
        return f"[HTTP error: {e}]"
    except Exception as e:
        return f"[Error: {e}]"

def safe_execute(code):
    buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
    try:
        exec(code, {}, {})
    except Exception as e:
        sys.stdout = old
        return f"[Code error: {e}]"
    sys.stdout = old
    return buf.getvalue().strip() or "[No output]"

def extract_code(text):
    # run: ... or ```python ... ```
    m = re.search(r'(?i)(?:run:|execute:|python:)\s*(.*)', text)
    if m: return m.group(1)
    m = re.search(r'```(?:python)?\s*([\s\S]*?)```', text)
    return m.group(1) if m else None
