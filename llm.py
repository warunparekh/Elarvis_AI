# llm.py

import os
import sys
import io
import re
import requests
from db import load_messages, get_persona

# ─── Configuration ────────────────────────────────
HF_TOKEN   = "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"
MODEL_ID   = "meta-llama/Llama-2-7b-chat-hf"
API_URL    = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS    = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant; you are Jarvis. "
    "Developer is Elarvis. Be witty, friendly, curious, and adaptive."
)

# ─── Helpers ────────────────────────────────────────
def build_prompt(convo_id, user_prompt):
    persona = get_persona(convo_id, DEFAULT_PERSONA)
    history = load_messages(convo_id)
    prompt = persona + "\n\n"
    for role, content in history:
        speaker = "User" if role == "user" else "Jarvis"
        prompt += f"{speaker}: {content}\n"
    prompt += f"User: {user_prompt}\nJarvis:"
    return prompt

def huggingface_chat(convo_id, user_prompt):
    prompt = build_prompt(convo_id, user_prompt)
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 300, "temperature": 0.7},
        "options": {"use_cache": False}
    }
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
        completion = resp.json()
        # HF returns [{"generated_text":"..."}]
        text = completion[0].get("generated_text", "")
        # strip the prompt from the response
        return text[len(prompt):].strip()
    except Exception as e:
        msg = str(e)
        if "401" in msg or "403" in msg:
            return "[Model error: Invalid or missing HF_TOKEN]"
        return f"[Model error: {e}]"

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
    # run: python: ```python ...
    m = re.search(r'(?i)(?:run:|execute:|python:)\s*(.*)', text)
    if m: return m.group(1)
    m = re.search(r'```(?:python)?\s*([\s\S]*?)```', text)
    return m.group(1) if m else None
