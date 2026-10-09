"""Step 1: read knowledge_base.json AND confluence_pages.json,
and turn everything into LangChain Documents."""

import json
import os

import config


# ---------- Part 1: FAQ file ----------

def load_entries(path):
    """Return a plain list of dicts: {category, question, answer}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for block in data["knowledge_base"]:
        for qa in block["questions"]:
            entries.append({
                "category": block["category"].title(),
                "question": qa["question"].strip(),
                "answer": qa["answer"].strip(),
            })
    return entries


def load_faq_documents(path):
    """Each FAQ becomes one Document."""
    from langchain_core.documents import Document

    docs = []
    for e in load_entries(path):
        text = f"Question: {e['question']}\nAnswer: {e['answer']}"
        docs.append(Document(
            page_content=text,
            metadata={"category": e["category"], "question": e["question"]},
        ))
    return docs


# ---------- Part 2: Confluence pages (downloaded through MCP) ----------

def load_confluence_documents(path):
    """Each Confluence page is cut into small chunks. Each chunk becomes one Document."""
    if not os.path.exists(path):
        return []          # no Confluence file yet -> nothing to add

    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    with open(path, encoding="utf-8") as f:
        pages = json.load(f)

    docs = []
    for page in pages:
        if page["title"] in config.SKIP_TITLES:
            continue       # skip Atlassian's default template pages

        for chunk in splitter.split_text(page["content"]):
            docs.append(Document(
                page_content=f"Page: {page['title']}\n{chunk}",
                metadata={
                    "category": "Confluence",
                    "question": f"Confluence: {page['title']}",   # shown by the 'show' command
                    "url": page.get("url", ""),
                },
            ))
    return docs


# ---------- Put both together ----------

def load_documents(path):
    """FAQ documents + Confluence documents."""
    docs = load_faq_documents(path)
    docs.extend(load_confluence_documents(config.CONFLUENCE_FILE))
    return docs


if __name__ == "__main__":
    print("FAQ entries:", len(load_entries(config.DATA_FILE)))
    conf_docs = load_confluence_documents(config.CONFLUENCE_FILE)
    print("Confluence chunks:", len(conf_docs))
    print("From pages:", sorted({d.metadata["question"] for d in conf_docs}))