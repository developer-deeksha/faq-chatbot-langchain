"""Step 2 (run ONCE, or again whenever the JSON changes):
embed every FAQ and save a FAISS search index to the vectorstore/ folder."""

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

import config
from load_data import load_documents


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


def main():
    docs = load_documents(config.DATA_FILE)
    print(f"Loaded {len(docs)} FAQ entries. Creating embeddings (first run downloads the model)...")
    store = FAISS.from_documents(docs, get_embeddings())
    store.save_local(config.VECTORSTORE_DIR)
    print(f"Done. Index saved in '{config.VECTORSTORE_DIR}/'")


if __name__ == "__main__":
    main()
