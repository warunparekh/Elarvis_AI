# HF_TOKEN   = "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"
# llm.py
import os, sys, io, re, requests
from db import load_messages, get_persona

# ─── Configuration ────────────────────────────────────
HF_TOKEN = "YOUR_TOKEN"
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN not set! You must export your Hugging Face token as HF_TOKEN "
        "(see https://huggingface.co/settings/tokens)."
    )

MODEL_ID = "lmsys/vicuna-7b-v1.5"
API_URL  = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
HEADERS  = {"Authorization": f"Bearer {HF_TOKEN}"}

DEFAULT_PERSONA = (
    "Your name is Jarvis. Never call yourself AI or assistant — you are Jarvis. "
    "Your developer is Elarvis. Be witty, friendly, curious, and adaptive."
)

def build_prompt(convo_id, user_prompt):
    persona = get_persona(convo_id, DEFAULT_PERSONA)
    history = load_messages(convo_id)
    prompt = persona + "\n"
    # Include last 3 exchanges
    for role, content in history[-3:]:
        speaker = "User" if role=="user" else "Jarvis"
        prompt += f"{speaker}: {content}\n"
    prompt += f"User: {user_prompt}\nJarvis:"
    return prompt

def huggingface_chat(convo_id, user_prompt):
    prompt = build_prompt(convo_id, user_prompt)
    payload = {"inputs": prompt}
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # HF returns {"generated_text": "..."} for text-generation endpoints
        text = data.get("generated_text", "")
        if text.startswith(prompt):
            return text[len(prompt):].strip()
        return text.strip()
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 404:
            return "[Model error: endpoint not found — check MODEL_ID]"
        if code in (401,403):
            return "[Model error: invalid or expired HF_TOKEN]"
        return f"[HTTP error {code}: {e}]"
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
    m = re.search(r'(?i)(?:run:|execute:|python:)\s*(.*)', text)
    if m: return m.group(1)
    m = re.search(r'```(?:python)?\s*([\s\S]*?)```', text)
    return m.group(1) if m else None
