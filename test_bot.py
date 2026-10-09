"""Automatic tests.  Run:  python test_bot.py

TEST 1 (data):      the JSON loads correctly.
TEST 2 (retrieval): for each sample question, the right FAQ must be in the top 3 results.
TEST 3 (unknown):   off-topic questions must be rejected (distance above MAX_DISTANCE).

These tests do NOT need Ollama - they only test the search part.
"""

import config
from load_data import load_entries

# (what a customer might type, FAQ question(s) that would be a correct hit)
RETRIEVAL_CASES = [
    ("I forgot my password",               ["how do i reset my member password?"]),
    ("can I use PayPal to pay",            ["how do i pay with paypal?"]),
    ("when will my card be charged",       ["when will i be charged for my order?"]),
    ("can I change my delivery address",   ["can i change the shipping address on my order?"]),
    ("do you ship outside the US",         ["can i ship my order internationally?"]),
    ("how do I check my gift card balance",["how do i check my gift card balance?"]),
    ("how long do you keep my pickup order",["how long will you hold my order?",
                                             "how long will my order be held?"]),
    ("do you accept Discover cards",       ["what are the payment options?"]),
    ("how do I join as a member",          ["how do i become a member?"]),
]

OFF_TOPIC = ["who won the cricket world cup", "write a python program",
             "what is the capital of france", "my name is deeksha"]


def test_data():
    entries = load_entries(config.DATA_FILE)
    assert len(entries) == 71, f"expected 71 FAQs, got {len(entries)}"
    assert all(e["question"] and e["answer"] for e in entries)
    print(f"[PASS] data: {len(entries)} FAQ entries loaded")


def test_retrieval_and_unknown():
    from langchain_community.vectorstores import FAISS
    from build_index import get_embeddings
    store = FAISS.load_local(config.VECTORSTORE_DIR, get_embeddings(),
                             allow_dangerous_deserialization=True)

    passed = 0
    for query, accepted in RETRIEVAL_CASES:
        results = store.similarity_search_with_score(query, k=config.TOP_K)
        found = [d.metadata["question"].lower() for d, _ in results]
        ok = any(a in found for a in accepted)
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] '{query}'  best distance={results[0][1]:.2f}  top hit='{found[0]}'")
    print(f"retrieval: {passed}/{len(RETRIEVAL_CASES)} passed\n")

    good = []
    for query, _ in RETRIEVAL_CASES:
        good.append(store.similarity_search_with_score(query, k=1)[0][1])
    print(f"worst on-topic distance: {max(good):.2f}  (MAX_DISTANCE = {config.MAX_DISTANCE})")

    rejected = 0
    for query in OFF_TOPIC:
        dist = store.similarity_search_with_score(query, k=1)[0][1]
        ok = dist > config.MAX_DISTANCE
        rejected += ok
        print(f"[{'PASS' if ok else 'FAIL'}] off-topic '{query}'  distance={dist:.2f}")
    print(f"off-topic rejected: {rejected}/{len(OFF_TOPIC)}")
    print("\nTip: if off-topic FAILs, lower MAX_DISTANCE in config.py; "
          "if on-topic questions get rejected, raise it. "
          "Pick a value between the worst on-topic and best off-topic distance.")


if __name__ == "__main__":
    test_data()
    test_retrieval_and_unknown()
