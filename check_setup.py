"""Run:  python check_setup.py
Checks every piece the chatbot needs and tells you exactly what to fix.
Uses only the Python standard library, so it works even if other things are broken."""

import json
import os
import urllib.request

import config

HOST = "http://127.0.0.1:11434"


def ok(msg):   print(f"[ OK ] {msg}")
def bad(msg):  print(f"[FAIL] {msg}")


def main():
    print("--- 1. Project files ---")
    here = os.path.dirname(os.path.abspath(__file__))
    print("Running from folder:", here)
    text = open(os.path.join(here, "chatbot.py"), encoding="utf-8").read()
    if "model is offline" in text:
        ok("chatbot.py is the UPDATED version")
    else:
        bad("chatbot.py is the OLD version -> replace it with the new file, in THIS folder")
    if os.path.exists(os.path.join(here, config.VECTORSTORE_DIR, "index.faiss")):
        ok("search index exists")
    else:
        bad("search index missing -> run: python build_index.py")

    print("\n--- 2. Ollama server ---")
    try:
        with urllib.request.urlopen(HOST + "/api/tags", timeout=3) as r:
            models = [m["name"] for m in json.load(r).get("models", [])]
        ok(f"Ollama is running at {HOST}")
    except Exception as err:
        bad(f"Cannot reach Ollama at {HOST}  ({err})")
        print("       -> Open a NEW terminal and run:  ollama serve   (leave it open)")
        print("       -> Or start the 'Ollama' app from the Windows Start menu")
        print("       -> Not installed? https://ollama.com/download  (then reopen the terminal)")
        print("       -> If you use a VPN/proxy, run:  set NO_PROXY=127.0.0.1,localhost")
        return

    print("\n--- 3. Model ---")
    print("Installed models:", models or "none")
    if any(m.split(":")[0] == config.LLM_MODEL.split(":")[0] for m in models):
        ok(f"'{config.LLM_MODEL}' is installed")
    else:
        bad(f"'{config.LLM_MODEL}' not installed -> run:  ollama pull {config.LLM_MODEL}")
        return

    print("\n--- 4. Test generation (can take a while the first time) ---")
    try:
        req = urllib.request.Request(
            HOST + "/api/generate",
            data=json.dumps({"model": config.LLM_MODEL, "prompt": "Say hi in 3 words.",
                             "stream": False}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            ok("Model replied: " + json.load(r)["response"].strip())
    except Exception as err:
        bad(f"Generation failed: {err}")
        return

    print("\nAll good. Now run:  python main.py")


if __name__ == "__main__":
    main()
