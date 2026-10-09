"""All settings in one place. Change values here, nothing else needs editing."""

DATA_FILE = "data/knowledge_base.json"
VECTORSTORE_DIR = "vectorstore"          # folder where the search index is saved

# Open-source embedding model (downloads once, ~90 MB, runs on your CPU)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Open-source LLM served locally by Ollama (run: ollama pull llama3.2)
LLM_MODEL = "llama3.2"
LLM_TEMPERATURE = 0          # 0 = stick to the facts, no creativity

TOP_K = 3                    # how many FAQ entries to give the LLM
MAX_DISTANCE = 1.0           # larger distance = worse match. Above this => "I don't know"
                             # (run test_bot.py to see real numbers and tune this)
MAX_HISTORY_TURNS = 4        # how many past Q&A pairs the bot remembers

# ---- Confluence (downloaded through MCP) ----
CONFLUENCE_FILE = "data/confluence_pages.json"   # created by download_pages.py
CHUNK_SIZE = 800          # long pages are cut into pieces of about this many characters
CHUNK_OVERLAP = 100       # pieces share a little text so no sentence is lost at the cut

# Atlassian's default sample pages. We do not index them. Make this list empty [] to index everything.
SKIP_TITLES = ["Explore Confluence Features", "Getting started in Confluence", "Overview"]
