"""The chatbot brain (RAG = Retrieval Augmented Generation):
1. handle greetings / small talk without searching
2. find the FAQ entries most similar to the question
3. a "grader" step checks the FAQ really answers the question (small models need this)
4. the local LLM writes the answer using ONLY those FAQ entries
"""

import re

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

import config
from build_index import get_embeddings

NO_ANSWER = ("Sorry, I couldn't find that in our help articles. "
             "I can help with membership, payments, orders, shipping and returns. "
             "Please rephrase your question or contact our support team.")

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """You are a friendly customer support assistant.
Answer the customer's question using ONLY the help-center information below.
- Be short and clear. Keep step-by-step instructions as numbered steps.
- If the information does not contain the answer, reply exactly: I don't know.
- Never invent policies, prices, or time limits.

Help-center information:
{context}

Conversation so far:
{history}

Customer question: {question}
Answer:"""
)

REWRITE_PROMPT = ChatPromptTemplate.from_template(
    """Your job: make the customer's last message understandable on its own.
- ONLY if it is a short follow-up that depends on the conversation (like "what about PO boxes?"
  or "and how long does it take?"), rewrite it as a complete question.
- If it is a new question, a statement, a greeting, or about something unrelated, repeat it EXACTLY unchanged.
Reply with the message only, no explanation.

Conversation:
{history}

Last message: {question}
Result:"""
)

GRADE_PROMPT = ChatPromptTemplate.from_template(
    """Decide if the help-center information below contains the answer to the customer's message.
Reply with one word only: YES or NO.
Reply NO if the message is a statement, small talk, or about a topic the information does not cover.

Help-center information:
{context}

Conversation so far:
{history}

Customer message: {question}
Contains the answer (YES or NO):"""
)

# ---------- small talk (no LLM needed) ----------
GREETINGS = {"hi", "hello", "hey", "hii", "hiii", "good morning", "good afternoon",
             "good evening", "hello there", "hi there", "hey there"}
THANKS = {"thanks", "thank you", "thankyou", "thanks a lot", "thank you so much", "ok thanks"}
BYES = {"bye", "goodbye", "see you", "see ya"}
HELP = "I can help with membership, payments, orders, shipping and returns."


def small_talk(text):
    """Return a canned reply for greetings/thanks/names, otherwise None."""
    t = re.sub(r"[^a-z ]", "", text.lower()).strip()
    if t in GREETINGS:
        return f"Hi! 👋 {HELP} What would you like to know?"
    if t in THANKS:
        return "You're welcome! Anything else I can help with?"
    if t in BYES:
        return "Goodbye! Have a great day."
    m = re.match(r"^(my name is|i am|im|i'm|this is)\s+([a-z]+)$", text.lower().strip(" .!"))
    if m:
        return f"Nice to meet you, {m.group(2).title()}! {HELP} What would you like to know?"
    if t in ("who are you", "what can you do", "help"):
        return f"I'm the support assistant. {HELP}"
    return None


class FAQBot:
    def __init__(self):
        self.store = FAISS.load_local(
            config.VECTORSTORE_DIR, get_embeddings(),
            allow_dangerous_deserialization=True,  # safe: we created this file ourselves
        )
        llm = ChatOllama(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)
        self.answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
        self.rewrite_chain = REWRITE_PROMPT | llm | StrOutputParser()
        self.grade_chain = GRADE_PROMPT | llm | StrOutputParser()
        self.history = []          # list of (question, answer) - only successful answers

    # ---------- helpers ----------
    def _history_text(self):
        recent = self.history[-config.MAX_HISTORY_TURNS:]
        return "\n".join(f"Customer: {q}\nAssistant: {a}" for q, a in recent) or "(none)"

    def retrieve(self, query):
        """Return [(Document, distance)] for good matches only. Lower distance = better."""
        results = self.store.similarity_search_with_score(query, k=config.TOP_K)
        return [(d, s) for d, s in results if s <= config.MAX_DISTANCE]

    def _is_relevant(self, question, context):
        verdict = self.grade_chain.invoke({
            "context": context, "history": self._history_text(), "question": question})
        return verdict.strip().upper().startswith("YES")

    # ---------- main entry ----------
    def ask(self, question):
        reply = small_talk(question)
        if reply:
            return reply, []

        matches = []
        try:
            search_query = question
            if self.history:   # make follow-ups like "what about PO boxes?" searchable
                search_query = self.rewrite_chain.invoke(
                    {"history": self._history_text(), "question": question}).strip()

            matches = self.retrieve(search_query)
            context = "\n\n".join(d.page_content for d, _ in matches)

            if not matches or not self._is_relevant(question, context):
                return NO_ANSWER, []

            answer = self.answer_chain.invoke({
                "context": context,
                "history": self._history_text(),
                "question": search_query,
            }).strip()
            if answer.lower().startswith("i don't know"):
                return NO_ANSWER, []

        except Exception:
            # LLM (Ollama) not reachable -> still help by returning the best FAQ answer as-is
            matches = self.retrieve(question)
            if not matches:
                return NO_ANSWER, []
            best = matches[0][0].page_content.split("\nAnswer: ", 1)[-1]
            return (best + "\n\n(Note: the AI model is offline, so this is the raw FAQ answer.)",
                    [d.metadata["question"] for d, _ in matches])

        self.history.append((question, answer))
        return answer, [d.metadata["question"] for d, _ in matches]
