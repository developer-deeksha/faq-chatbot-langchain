"""Step 3: talk to the bot in the terminal.   Run:  python main.py"""

import os
import sys

# Hide harmless Hugging Face messages. The embedding model is already downloaded
# (build_index.py did that), so chatting needs no internet for it.
# These lines must stay ABOVE the other imports.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import config


def ollama_running():
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return True
    except Exception:
        return False


def main():
    if not os.path.exists(os.path.join(config.VECTORSTORE_DIR, "index.faiss")):
        sys.exit("No search index found. Run first:  python build_index.py")

    if not ollama_running():
        print("WARNING: Ollama is not running, so I can only show raw FAQ answers.")
        print("   Fix: open the Ollama app (or run 'ollama serve' in another terminal),")
        print(f"   then run 'ollama pull {config.LLM_MODEL}' once, and restart this program.\n")

    try:
        from transformers.utils import logging as hf_logging
        hf_logging.set_verbosity_error()
        hf_logging.disable_progress_bar()
    except Exception:
        pass

    from chatbot import FAQBot   # imported late so the check above gives a clean message
    print("Loading chatbot...")
    bot = FAQBot()
    print("Support Bot ready! Type your question ('quit' to exit, 'show' toggles sources).\n")

    show_sources = False
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        if question.lower() == "show":
            show_sources = not show_sources
            print(f"(sources {'ON' if show_sources else 'OFF'})\n")
            continue

        try:
            answer, sources = bot.ask(question)
        except Exception as err:
            print(f"Error: {err}\nIs Ollama running? Try:  ollama serve   and   ollama pull {config.LLM_MODEL}\n")
            continue

        print(f"\nBot: {answer}\n")
        if show_sources and sources:
            print("   Used FAQ entries:", *[f"- {s}" for s in sources], sep="\n   ")
            print()


if __name__ == "__main__":
    main()