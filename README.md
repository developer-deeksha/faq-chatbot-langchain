# Support Chatbot (LangChain + Ollama + Confluence via MCP)

A support chatbot that answers questions using **only** your own content:

1. **FAQ file** - `data/knowledge_base.json` (71 FAQs: Membership, Payments, Returns, Orders/Shipping)
2. **Confluence pages** - downloaded through **MCP** (Model Context Protocol)

Everything runs on your own computer with open-source models. No LLM API key is needed.

## 1. How it works

```
 CONFLUENCE pages ──(MCP)──► download_pages.py ──► data/confluence_pages.json ─┐
                                                                               ├─► load_data.py ─► build_index.py ─► FAISS index
 data/knowledge_base.json (71 FAQs) ───────────────────────────────────────────┘

 your question ─► main.py ─► chatbot.py:
      1. small talk (hello / thanks / my name is ...)  -> fixed reply
      2. follow-up question?                           -> LLM rewrites it as a full question
      3. search the FAISS index for the 3 closest pieces (FAQs + Confluence chunks)
      4. drop weak matches (distance above MAX_DISTANCE)
      5. grader: LLM answers YES/NO "do these pieces answer the question?"
      6. answer: LLM writes the reply using ONLY those pieces
```

Why this design: the LLM never answers from its own memory, only from your FAQ and Confluence text,
so it does not invent policies. MCP is used only to **download** the pages. After that,
the chatbot works the same for both sources.

## 2. Project files

| File | Job |
|---|---|
| `config.py` | All settings (model names, thresholds, chunk size, skipped pages) |
| `load_data.py` | Reads the FAQ JSON and the Confluence JSON, makes LangChain `Document`s |
| `build_index.py` | Creates embeddings and saves the FAISS index (run after any data change) |
| `chatbot.py` | The RAG logic (`FAQBot` class): small talk, rewrite, search, grader, answer |
| `main.py` | Terminal chat loop - the file you run |
| `my_mcp_client.py` | MCP test: connects to Confluence and prints a few pages |
| `download_pages.py` | MCP download: saves all pages of your space to `data/confluence_pages.json` |
| `test_bot.py` | Automatic search-quality tests |
| `check_setup.py` | Checks Ollama, the model and the project files |
| `.env` | **Your secrets** (email, token, URL, space key). Never share it |
| `.env.example` | Template for `.env` |
| `data/knowledge_base.json` | The FAQ knowledge base |
| `data/confluence_pages.json` | Confluence pages (created by `download_pages.py`) |
| `vectorstore/` | The saved search index (created by `build_index.py`) |

## 3. One-time setup

**A. Python** 3.10 or newer: `python --version`

**B. Ollama** (runs the local LLM): https://ollama.com/download
```bash
ollama pull llama3.2
```
Make sure the Ollama app is running (llama icon in the system tray) or run `ollama serve`.

**C. Virtual environment and packages** (Windows PowerShell)
```bash
cd C:\faq-chatbot-langchain
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```
Mac/Linux: activate with `source venv/bin/activate`.

Every time you open a new terminal, only repeat `cd` and `venv\Scripts\activate`.

## 4. Connect Confluence through MCP

**What is MCP?** A standard way for your program (the *client*) to use an outside tool through a helper
program (the *server*). Here the server is the open-source `mcp-atlassian` (not an official
Atlassian product). `my_mcp_client.py` and `download_pages.py` are the client. The server is started
automatically with `uvx`.

**Step 1 - Create a Confluence site, a space, and a few pages** (a free plan is available; check the current limits on Atlassian's pricing page).

**Step 2 - Create an API token**
Open https://id.atlassian.com/manage-profile/security/api-tokens and click **Create API token**.
Copy it immediately (shown once).

**Step 3 - Create the `.env` file** in the project folder
```
CONFLUENCE_URL=https://YOUR-SITE.atlassian.net/wiki
CONFLUENCE_USERNAME=your-atlassian-login-email
CONFLUENCE_API_TOKEN=your-token
CONFLUENCE_SPACE_KEY=YOURKEY
```
- No quote marks and no spaces around `=`.
- The URL must end with `/wiki`.
- `CONFLUENCE_USERNAME` is your Atlassian **login email**, not your site name.
- The space key is the part after `/spaces/` in a page URL. Personal spaces look like `~7120...`; keep the `~`.

**Step 4 - Test the MCP connection**
```bash
python my_mcp_client.py
```
Expected: `Connected to MCP server!`, the tools `confluence_search` and `confluence_get_page`,
and a search result with your page data. The first run takes 1-2 minutes (the server is downloaded).

**Step 5 - Download all pages**
```bash
python download_pages.py
```
Expected: a list of your pages with character counts, then `Saved N pages to data/confluence_pages.json`.

**Step 6 - Build the search index** (FAQs + Confluence together)
```bash
python load_data.py       # quick check: prints FAQ count and Confluence chunk count
python build_index.py
```

Atlassian's default sample pages ("Explore Confluence Features", "Getting started in Confluence",
"Overview") are skipped through `SKIP_TITLES` in `config.py`. Set it to `[]` to index everything.

## 5. Run the chatbot
```bash
python main.py
```
Commands: `show` (toggle display of the sources used for each answer), `quit`.

Examples:
```
You: How many days of leave do I get?        -> answered from your Confluence "Leave Policy" page
You: What are the payment options?           -> answered from the FAQ file
You: Who won the cricket world cup?          -> "Sorry, I couldn't find that..."
```

## 6. When your Confluence pages change

The chatbot reads a saved copy, so edits in Confluence do not appear automatically:
```bash
python download_pages.py
python build_index.py
```
Then restart `python main.py`. The same two steps apply after editing `knowledge_base.json`
(only `build_index.py` is needed then).

## 7. Testing

**Setup check:** `python check_setup.py` checks the project files, Ollama, the model and a test reply.

**Search-quality test (no Ollama needed):** `python test_bot.py`
It checks that the FAQ JSON loads, that differently-worded FAQ questions find the right FAQ in the top 3,
and that off-topic questions are far away. It prints distance scores (lower = better match).
Tune `MAX_DISTANCE` in `config.py` between the worst on-topic and the best off-topic distance.
Confluence chunks are longer than FAQs, so they may need a slightly larger value.

**Manual test:** run `python main.py`, type `show`, then try one question per Confluence page,
one FAQ question, a follow-up question, and an off-topic question.

## 8. Common problems

| Problem | Fix |
|---|---|
| `No module named 'mcp'` | Activate the venv, then `python -m pip install -r requirements.txt` |
| `Something is missing in your .env file` | A value in `.env` is missing or blank |
| 401 / Unauthorized from Confluence | Wrong email or token. The email must be your Atlassian login email; create a new token if unsure |
| Search finds no pages | Wrong `CONFLUENCE_SPACE_KEY` (copy it again, keep the `~`) or the space has no pages |
| `uvx` not found | `python -m pip install uv`, with the venv active |
| `No search index found` | Run `python build_index.py` |
| Connection refused / Ollama error | Start the Ollama app or `ollama serve`; run `python check_setup.py` |
| A Confluence question gets "couldn't find" | Raise `MAX_DISTANCE` slightly, or ask using words closer to the page text |
| The bot answers off-topic things | Lower `MAX_DISTANCE` |
| Old answers after editing Confluence | Run `download_pages.py` then `build_index.py`, and restart `main.py` |

## 9. Security
- Never share or commit `.env` or your API token. `.env` is listed in `.gitignore`.
- `data/confluence_pages.json` contains your Confluence content. Keep it private.
- If a token leaks, delete it on the Atlassian API tokens page and create a new one.
- The MCP server is started with only the two read-only tools (`confluence_search`, `confluence_get_page`).

## 10. Limitations and ideas
- Confluence data is a **snapshot** (it needs a re-sync to refresh).
- One search returns up to 50 pages; larger spaces need more searches.
- The small local LLM is less reliable than large models, which is why the grader step exists.

Ideas: show the Confluence page link in answers, a `sync` command inside the chat,
a live mode where the bot calls Confluence through MCP at question time, a Streamlit web UI.
