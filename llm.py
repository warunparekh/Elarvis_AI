# llm.py
import ollama, sys, io, re
from db import load_messages, get_persona

MODEL_NAME    = "deepseek-coder"
DEFAULT_PERSONA = (
  "Your name is Jarvis. Never call yourself AI; only Jarvis. "
  "Developer is Elarvis. Be witty, friendly, curious, adaptive."
)

def build_messages(convo_id,user_prompt):
    persona = get_persona(convo_id, DEFAULT_PERSONA)
    history = load_messages(convo_id)
    msgs = [{"role":"system","content":persona}]
    msgs += [{"role":r,"content":c} for r,c in history]
    msgs.append({"role":"user","content":user_prompt})
    return msgs

def ollama_chat(messages):
    try:
        stream = ollama.chat(model=MODEL_NAME, messages=messages, stream=True)
        out=[]
        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                out.append(chunk["message"]["content"])
        return "".join(out).strip()
    except Exception as e:
        return f"[Model error: {e}]"

def safe_execute(code):
    buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
    try:
        exec(code,{},{})
    except Exception as e:
        sys.stdout = old
        return f"[Code error: {e}]"
    sys.stdout = old
    return buf.getvalue().strip() or "[No output]"

def extract_code(text):
    m = re.search(r'(?i)(?:run:|execute:|python:)\s*(.*)', text)
    if m: return m.group(1)
    m = re.search(r'```(?:python)?\s*([\s\S]*?)```', text)
    if m: return m.group(1)
    return None
