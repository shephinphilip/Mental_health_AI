#!pip install langchain langchain-core langchain-community==0.3.22 langchain-openai==0.2.0 faiss-cpu

# ============================================================
#  Child Adaptive RAG Chatbot with LangChain Memory Integration
# ============================================================

import re, random, datetime, torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
from openai import OpenAI
import os

# LangChain imports
from langchain.memory import ConversationSummaryMemory
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

llm =  ChatOpenAI(model="gpt-4o-mini",api_key=os.getenv('OPENAI_API_KEY'))

# ─────────────────────────────
#  CONTEXT AREAS (from clinical guidelines)
# ─────────────────────────────
CONTEXT_AREAS = {
    "family": [
        "father", "mother", "parents", "siblings", "home",
        "caretaker", "discipline", "attachment", "conflict"
    ],
    "school": [
        "teacher", "exam", "homework", "study", "grades", "learning",
        "attention", "classmates", "bullying", "school refusal"
    ],
    "peer_relations": [
        "friends", "best friend", "play", "isolation", "group",
        "social media", "peer pressure", "trust", "rejection"
    ],
    "developmental_history": [
        "speech", "language", "toilet training", "temper tantrums",
        "sleep patterns", "feeding habits", "milestones"
    ],
    "medical_physical": [
        "illness", "pain", "fatigue", "sleep", "headache", "stomach",
        "appetite", "energy", "body image"
    ],
    "emotional_functioning": [
        "sad", "fear", "anger", "mood", "worry", "hopeless", "irritable",
        "crying", "self-esteem"
    ],
    "environmental_stressors": [
        "neighbour", "violence", "financial", "housing", "community",
        "trauma", "migration", "loss"
    ],
    "cognitive_behavioral": [
        "thinking", "focus", "memory", "concentration",
        "obsession", "compulsion", "intrusive thoughts"
    ],
    "social_support": [
        "friends", "relatives", "counsellor", "teacher support",
        "safe space", "trust", "guidance"
    ]
}

# ─────────────────────────────
#  TOPIC TRACKER
# ─────────────────────────────
class TopicTracker:
    def __init__(self):
        self.last_area = None
        self.repeat_count = 0
    def detect_area(self, text):
        t = text.lower()
        for area, kws in CONTEXT_AREAS.items():
            if any(k in t for k in kws):
                return area
        return "other"
    def update(self, text):
        area = self.detect_area(text)
        if area == self.last_area:
            self.repeat_count += 1
        else:
            self.repeat_count = 1
            self.last_area = area
        return area, self.repeat_count

tracker = TopicTracker()

# ─────────────────────────────
#  EMBEDDING MODEL
# ─────────────────────────────
tok = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
mdl = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

def embed_texts(texts):
    toks = tok(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        out = mdl(**toks)
        return out.last_hidden_state.mean(dim=1).numpy()

# ─────────────────────────────
#  BUILD RAG CONTEXT
#  (load your empathic JSON dataset before running)
# ─────────────────────────────
import json
DATA_PATH = "combined_dataset.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)["dataset"]

CORPUS, META = [], []
for d in DATA:
    text = f"{d['category']} | {d['system_prompt']} {d['empathic_response']} {d['empathic_question']} {d['next_question']}"
    CORPUS.append(text)
    META.append(d)

CORPUS_EMB = embed_texts(CORPUS)

def retrieve_context(query, top_k=3):
    q_emb = embed_texts([query])
    sims = cosine_similarity(q_emb, CORPUS_EMB)[0]
    idxs = sims.argsort()[-top_k:][::-1]
    return [META[i] for i in idxs]

# ─────────────────────────────
#  LANGCHAIN MEMORY INTEGRATION
# ─────────────────────────────
embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_texts(["start"], embedder)

summary_memory = ConversationSummaryMemory(
    llm=ChatOpenAI(model="gpt-4o-mini", api_key=llm),
    input_key="question"  # <── crucial line
)
buffer_memory = ConversationBufferMemory(return_messages=True)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
rag_chain = ConversationalRetrievalChain.from_llm(
    ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=llm),
    retriever=retriever,
    memory=summary_memory
)

# ─────────────────────────────
#  RESPONSE GENERATOR
# ─────────────────────────────
def generate_response(user_text):
    # store in long-term vector memory
    vectorstore.add_texts([user_text])

    # detect area and repetition
    area, rep = tracker.update(user_text)

    if rep >= 3:
        next_area = random.choice([a for a in CONTEXT_AREAS.keys() if a != area])
        transition_prompt = f"The child has been talking mostly about {area}. Gently move to {next_area} next."
    else:
        transition_prompt = ""

    context_items = retrieve_context(user_text)
    context_text = "\n".join([
        f"Category: {c['category']}\nEmpathy: {c['empathic_response']}\nQuestion: {c['empathic_question']}\nFollow-up: {c['next_question']}"
        for c in context_items
    ])

    # combine RAG + memory summary context
    memory_context = summary_memory.load_memory_variables({}).get("history", "")
    combined_prompt = f"""
You are a compassionate, age-appropriate AI counselor for children aged 10–17.
Use natural, emotionally intelligent language. Avoid repetition.

Recent conversation summary:
{memory_context}

Relevant empathy dataset context:
{context_text}

Child said: "{user_text}"

{transition_prompt}

Respond with one caring reflection and one thoughtful follow-up question.
    """

    # run LangChain retrieval + LLM
    result = rag_chain.invoke({"question": combined_prompt, "chat_history": []})
    response = result["answer"] if isinstance(result, dict) else str(result)

    return response.strip()


import json, os, datetime

# ─────────────────────────────
#  SAVE CHAT AS JSON
# ─────────────────────────────
def save_conversation(conversation):
    """Save conversation turns into a timestamped JSON file."""
    folder = "/content/chat_sessions"
    os.makedirs(folder, exist_ok=True)
    fname = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(folder, fname)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)

    print(f"📄 Conversation saved as: {path}")


# ─────────────────────────────
#  MAIN CHAT LOOP
# ─────────────────────────────
def run_chat():
    print("=== Child Adaptive RAG Mental Health Chat (with Memory) ===")
    print("Type 'exit' to stop manually.\n")

    conversation = []
    max_questions = 10 #for testing purpose we reduced from 30 to 10
    question_count = 0

    while True:
        user = input("You: ").strip()
        if not user:
            continue
        if user.lower() == "exit":
            print("\nAI: That’s okay! We can stop anytime. Take care and remember, you matter.\n")
            break

        reply = generate_response(user)
        question_count += 1
        conversation.append({"user": user, "ai": reply})
        print(f"\nAI: {reply}\n")

        if question_count >= max_questions:
            goodbye_msg = (
                "We’ve talked about a lot today. "
                "Let’s take a pause for now — I really enjoyed hearing from you. "
                "Remember, you’re doing your best, and that matters. "
                "Goodbye for now, and take care of yourself."
            )
            print(f"\nAI: {goodbye_msg}\n")
            conversation.append({"ai": goodbye_msg})
            break

    return conversation


# ─────────────────────────────
#  RUN
# ─────────────────────────────
if __name__ == "__main__":
    convo = run_chat()
    save_conversation(convo)
