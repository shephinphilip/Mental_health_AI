import os
from typing import Dict, List, Optional,Tuple
import logging
import openai
import streamlit as st
from io import BytesIO
import time
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from docx import Document
from depression_question_pool import question_pool
from depression_scoring_guide import scoring_guides
from welcome_questions import welcome_questions
from dotenv import load_dotenv
from functools import lru_cache
from collections import defaultdict

# Load environment variables
load_dotenv()
# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)



# --- Critical items to front-load (safety first)
CRITICAL_IDS = {"phq9_9", "kads_7", "cesd_9"}  # you can add more if needed

# --- Minimal targets per category (rough #items that gives a stable estimate)
CATEGORY_TARGETS = {
    "depression": 9,  # PHQ-9 anchor
    "anxiety": 7,     # GAD-7 anchor
    "ptsd": 8,        # PCL-5 short set
    "ocd": 10,        # OCI-R short probe
    "bipolar": 7,     # MDQ core
}

# --- Core instruments per category (bonus to complete a clinically standard short form)
CORE_ANCHORS = {
    "depression": {"phq9", "kads11", "cesd", "mfqsf", "dass21"},  # any of these helps, PHQ-9 preferred
    "anxiety": {"gad7", "hads", "scared", "scas", "rcads", "dass21", "dassy"},
    "ptsd": {"pcl5", "iesr"},
    "ocd": {"oci_r", "ybocs"},
    "bipolar": {"mdq", "bsds"},
}


# --- Utility weights (tune these if you like)
W_NEED      = 2.0   # how much we value covering under-sampled categories
W_CORE      = 1.0   # bonus for core/anchor instruments
W_NOVELTY   = 0.3   # small bonus for switching instruments (less fatigue/narrowing)
W_DISCRIM   = 0.7   # prefer items in the top-2 categories when the margin is small


def load_document_content(filename):
    doc = Document(filename)
    return "\n".join([para.text for para in doc.paragraphs])

DOCUMENT_CONTENT = load_document_content("AI_Training_Document.docx")

# Configure logging
logging.basicConfig(filename="openai_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize LangChain RAG components
@st.cache_resource
def setup_rag():
    """Set up LangChain RAG with FAISS vector store."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=lambda text: len(text)
    )
    documents = text_splitter.create_documents([DOCUMENT_CONTENT])
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

def call_openai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        # Reset error flags on success
        st.session_state.pop("api_error", None)
        st.session_state.pop("connection_error", None)
        st.session_state.pop("rate_limit_error", None)
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        logging.error(f"OpenAI API returned an API Error: {e}")
        if "api_error" not in st.session_state:
            st.session_state.api_error = True
            st.error(f"Error communicating with OpenAI API: {e}. Please try again later.")
        return ""
    except openai.APIConnectionError as e:
        logging.warning(f"Connection error to OpenAI API: {e}. Retrying in 5 seconds...")
        time.sleep(5)
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            st.session_state.pop("connection_error", None)
            return response.choices[0].message.content.strip()
        except openai.APIConnectionError as e2:
            logging.error(f"Failed to connect to OpenAI API after retry: {e2}")
            if "connection_error" not in st.session_state:
                st.session_state.connection_error = True
                st.error(f"Unable to connect to OpenAI API: {e2}. Please check your internet connection and try again.")
            return ""
    except openai.RateLimitError as e:
        max_retries = 3
        for attempt in range(max_retries):
            delay = 2 ** attempt
            logging.warning(f"Rate limit error: {e}. Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                st.session_state.pop("rate_limit_error", None)
                return response.choices[0].message.content.strip()
            except openai.RateLimitError:
                continue
        logging.error(f"OpenAI API request exceeded rate limit after {max_retries} retries: {e}")
        if "rate_limit_error" not in st.session_state:
            st.session_state.rate_limit_error = True
            st.error(f"Rate limit exceeded for OpenAI API: {e}. Please wait a few minutes and try again.")
        return ""
    except openai.AuthenticationError as e:
        logging.error(f"Authentication error with OpenAI API: {e}")
        if "auth_error" not in st.session_state:
            st.session_state.auth_error = True
            st.error(f"Authentication failed for OpenAI API: {e}. Please check your API key.")
        return ""
    

    
def _instrument_key(qid: str, q: dict) -> str:
    """Infer instrument family; uses explicit field if present, else id prefix."""
    inst = (q.get("instrument") or "").strip().lower()
    if inst:
        return inst.replace(" ", "_").replace("-", "").replace("/", "_")
    ql = qid.lower()
    # common families
    for fam in ["phq9","kads","gad7","hads","hama","scas","scared","rcads","pcl5","iesr",
                "oci_r","ybocs","mdq","bsds","dass21","dassy","y_psc","ypsc","pdss","lsas"]:
        if ql.startswith(fam):
            return fam
    return "misc"

@lru_cache(maxsize=1)
def _id_to_item():
    return {q["id"]: q for q in question_pool}

def _max_per_item(q):
    sr = q.get("score_range") or []
    return max(sr) if sr else 0
    
def _normalized_answer(qid: str, raw_score: int) -> float:
    q = _id_to_item().get(qid)
    if not q:
        return 0.0
    m = _max_per_item(q)
    return (raw_score / m) if m > 0 else 0.0

    
def _category_stats(responses: Dict[str, int]):
    """Compute per-category coverage and mean severity (0..1) from answered items."""
    by_cat_sum = defaultdict(float)
    by_cat_cnt = defaultdict(int)
    by_inst_cnt = defaultdict(int)
    asked_ids = set()

    for qid, raw in responses.items():
        q = _id_to_item().get(qid)
        if not q:
            continue
        asked_ids.add(qid)
        cat = q["category"]
        by_cat_sum[cat] += _normalized_answer(qid, raw)
        by_cat_cnt[cat] += 1
        by_inst_cnt[_instrument_key(qid, q)] += 1

    # mean severity + coverage ratio
    mean = {c: (by_cat_sum[c] / by_cat_cnt[c]) if by_cat_cnt[c] else 0.0 for c in by_cat_cnt}
    cov  = {c: (by_cat_cnt[c] / CATEGORY_TARGETS.get(c, 6)) for c in by_cat_cnt}
    return asked_ids, mean, cov, by_inst_cnt    


def _top_two_categories(mean: Dict[str, float]) -> Tuple[Optional[str], Optional[str], float]:
    if not mean:
        return None, None, 1.0
    ranked = sorted(mean.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[0][0]
    second = ranked[1][0] if len(ranked) > 1 else None
    margin = (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else ranked[0][1]
    return top, second, margin


def get_critical_question(responses: Dict[str, int]) -> Optional[Dict]:
    """Ask critical/safety items ASAP if unanswered."""
    asked = set(responses.keys())
    for qid in CRITICAL_IDS:
        if qid not in asked and qid in _id_to_item():
            return _id_to_item()[qid]
    return None

def get_next_question(responses: Dict[str, int]) -> Optional[Dict]:
    """
    Deterministic, explainable next-question selector:
    1) Ask critical items first (suicidality etc.).
    2) Compute per-category mean severity & coverage from answered items.
    3) Score each remaining item by:
       score = W_NEED*(1 - cat_cov) + W_CORE*core_bonus + W_NOVELTY*novelty + W_DISCRIM*discrim
    4) Return argmax.
    """
    # 1) critical first
    crit = get_critical_question(responses)
    if crit:
        return crit

    # 2) stats from answered items
    asked_ids, mean, cov, by_inst_cnt = _category_stats(responses)
    top, second, margin = _top_two_categories(mean)
    # uncertain when margin is small
    uncertain = (margin < 0.20) if (top and second) else True

    # most recent instrument to avoid long streaks
    last_inst = None
    if responses:
        # pick the last answered qid in insertion order if dict preserves it; otherwise ignore
        last_qid = next(reversed(responses.keys()))
        last_q = _id_to_item().get(last_qid)
        if last_q:
            last_inst = _instrument_key(last_qid, last_q)

    # 3) candidates & utility
    best_q = None
    best_u = float("-inf")

    for q in question_pool:
        qid = q["id"]
        if qid in asked_ids:
            continue

        cat = q["category"]
        inst = _instrument_key(qid, q)

        # coverage need (prefer under-sampled categories)
        cat_cov = cov.get(cat, 0.0)
        need_term = (1.0 - min(1.0, cat_cov))  # 0..1

        # core bonus if this instrument anchors the category
        core_set = CORE_ANCHORS.get(cat, set())
        core_bonus = 1.0 if any(inst.startswith(k) for k in core_set) else 0.0

        # novelty if switching instruments
        novelty = 1.0 if (last_inst and inst != last_inst) else 0.0

        # discrimination bonus: when uncertain, prefer items from top-2; when certain, deepen top category
        if uncertain:
            discrim = 1.0 if (cat == top or cat == second) else 0.0
        else:
            discrim = 1.0 if (cat == top) else 0.0

        utility = (W_NEED * need_term) + (W_CORE * core_bonus) + (W_NOVELTY * novelty) + (W_DISCRIM * discrim)

        # small tie-breakers: prefer questions with bigger max score (more gradation), then by id
        utility += 0.01 * _max_per_item(q)

        if utility > best_u or (utility == best_u and qid < (best_q["id"] if best_q else "")):
            best_q, best_u = q, utility

    return best_q

def compute_scores(responses: Dict[str, int]) -> Dict[str, int]:
    scores = {
        "phq9": 0,
        "kads11": 0,
        "rcads_depression": 0,
        "dass21_depression": 0,
        "cesd": 0,
        "mfqsf": 0
    }
    for qid, score in responses.items():
        if qid.startswith("phq9_"):
            scores["phq9"] += score
        elif qid.startswith("kads_"):
            scores["kads11"] += score
        elif qid.startswith("rcads_dep_"):
            scores["rcads_depression"] += score
        elif qid.startswith("dass_dep_"):
            scores["dass21_depression"] += score
        elif qid.startswith("cesd_"):
            scores["cesd"] += score
        elif qid.startswith("mfqsf_"):
            scores["mfqsf"] += score
        else:
            logging.warning(f"Unrecognized question ID: {qid}")
    scores["dass21_depression"] *= 2
    return scores

def get_severity(score: int, tool: str) -> str:
    """Determine severity based on score and tool thresholds."""
    if tool in ["rcads_depression", "rcads_anxiety"]:
        return "Not applicable (requires T-score conversion)"
    if tool not in scoring_guides:
        return "Unknown"
    for min_score, max_score, severity in scoring_guides[tool]["thresholds"]:
        if min_score <= score <= max_score:
            return severity
    return "Unknown"




def generate_final_conclusion(scores: Dict[str, int], vector_store) -> Tuple[str, str, bytes, bytes]:

    if vector_store is None:
        return "Error: Vector store not initialized.", "", None, None

    # Critical summary
    critical_summary = {
        "phq9_9": f"{st.session_state.responses.get('phq9_9', 'Not answered')}/3",
        "kads_9": f"{st.session_state.responses.get('kads_9', 'Not answered')}/2",
        "rcads_dep_9": f"{st.session_state.responses.get('rcads_dep_9', 'Not answered')}/3",
        "dass_dep_7": f"{st.session_state.responses.get('dass_dep_7', 'Not answered')}/3",
        "cesd_9": f"{st.session_state.responses.get('cesd_9', 'Not answered')}/3",
    }

    # Determine primary category and severity
    severity_scores = {}
    for tool in scores:
        if tool in ["rcads_depression", "rcads_anxiety"]:
            continue
        severity = get_severity(scores.get(tool, 0), tool)
        if severity == "Unknown":
            continue
        thresholds = scoring_guides.get(tool, {}).get("thresholds", [])
        severity_index = 0
        for i, t in enumerate(thresholds):
            if t[2] == severity:
                severity_index = i
                break
        category = next((q["category"] for q in question_pool if q["id"].startswith(tool.split("_")[0])), "depression")
        severity_scores[category] = max(severity_scores.get(category, -1), severity_index)

    primary_category = max(severity_scores, key=severity_scores.get) if severity_scores else "depression"
    category_to_score_key = {"depression": "phq9", "anxiety": "hama", "ptsd": "pcl5"}
    score_key = category_to_score_key.get(primary_category, "phq9")
    severity = get_severity(scores.get(score_key, 0), score_key)

    # Retrieve context
    query = f"Guidelines for supporting adolescents with {primary_category} at {severity} severity."
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)

    context = "\n\n".join(doc.page_content for doc in docs)

    # Prompt template for two separate reports
    prompt_template = PromptTemplate(
    input_variables=["context", "critical_summary", "primary_category", "scores", "severity"],
    template="""
You are a licensed child psychiatrist preparing a clinical-style summary based on an assessment.
Avoid giving direct diagnoses or alarming language. Use neutral, observational tone.
Speak as if writing an assessment summary, not an email or advice column.

--- Parents' Report ---
Include:
- Observational summary of the child's current emotional/behavioral patterns based on assessment responses.
- Frame guidance as recommendations for creating a supportive environment, not commands.
- Avoid stating "your child has depression" — instead use language like "patterns consistent with mood-related challenges".
- Include when professional consultation *may* be beneficial without sounding urgent unless self-harm risk is flagged.

--- Child's Report ---
Include:
- Empathetic, age-appropriate message written in language suitable for an 8–15 year old.
- Avoid clinical terms, focus on reassurance and normalization of feelings.
- Encourage communication with trusted adults in gentle language.

Clinical Context:
{context}

Critical Responses:
{critical_summary}

Primary Category: {primary_category}
Scores: {scores}
Severity: {severity}
"""
)


    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
    combine_docs_chain = create_stuff_documents_chain(llm, prompt_template)
    rag_chain = create_retrieval_chain(vector_store.as_retriever(search_kwargs={"k": 3}), combine_docs_chain)

    result = rag_chain.invoke({
        "input": query,
        "context": context,
        "critical_summary": critical_summary,
        "primary_category": primary_category,
        "scores": scores,
        "severity": severity
    })

    full_text = result["answer"]

    # Split reports by markers
    if "--- Child's Report ---" in full_text:
        parents_text, child_text = full_text.split("--- Child's Report ---", 1)
        parents_text = parents_text.replace("--- Parents' Report ---", "").strip()
        child_text = child_text.strip()
    else:
        parents_text, child_text = full_text, ""

    # Generate PDF for Parents
    def create_pdf(content):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        for line in content.split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 12))
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

    parents_pdf = create_pdf(parents_text)
    child_pdf = create_pdf(child_text)

    return parents_text, child_text, parents_pdf, child_pdf




def main():
    st.title("Adolescent Mental Health Assessment")

    # Initialize session state variables
    if "phase" not in st.session_state:
        st.session_state.phase = "welcome"  # can be 'welcome' or 'diagnostic' or 'results'

    if "welcome_index" not in st.session_state:
        st.session_state.welcome_index = 0

    if "responses" not in st.session_state:
        st.session_state.responses = {}

    if "diagnostic_index" not in st.session_state:
        st.session_state.diagnostic_index = 0

    if "scores" not in st.session_state:
        st.session_state.scores = None

    MAX_DIAGNOSTIC_QUESTIONS = 15  # You can adjust based on desired length

    if st.session_state.phase == "welcome":
        # Ask welcome questions sequentially
        q = welcome_questions[st.session_state.welcome_index]
        st.write(q["text"])

        if q["type"] == "text":
            answer = st.text_input("Your answer:", key=f"welcome_{q['id']}")
        elif q["type"] == "radio":
            answer = st.radio("Select one:", q["options"], key=f"welcome_{q['id']}")
        else:
            answer = None  # Unsupported type here

        if st.button("Next", key=f"welcome_next_{q['id']}"):
            # Store welcome answers, no scoring needed
            if answer:
                st.session_state.responses[q["id"]] = answer
                st.session_state.welcome_index += 1
                if st.session_state.welcome_index >= len(welcome_questions):
                    st.session_state.phase = "diagnostic"
                    st.rerun()
                else:
                    st.rerun()
            else:
                st.warning("Please provide an answer to continue.")

    elif st.session_state.phase == "diagnostic":
        # adaptive selection, no LLM
        MAX_DIAGNOSTIC_QUESTIONS = 15  # keep your cap

        # Pick next question
        next_q = get_next_question(st.session_state.responses)

        # If done or cap reached -> results
        if next_q is None or len([k for k in st.session_state.responses if k in _id_to_item()]) >= MAX_DIAGNOSTIC_QUESTIONS:
            st.session_state.phase = "results"
            st.rerun()

        st.write(f"Question {len([k for k in st.session_state.responses if k in _id_to_item()]) + 1}: {next_q['text']}")
        ans = st.radio("Select an option:", next_q["options"], key=f"diag_{next_q['id']}")

        if st.button("Next", key=f"diag_next_{next_q['id']}"):
            if ans in next_q["options"]:
                idx = next_q["options"].index(ans)
                raw_score = next_q["score_range"][idx]
                st.session_state.responses[next_q["id"]] = raw_score

                # Optional early-stop example: if PHQ-9 core suggests moderate+ early
                # (use your own rules; this is just an example)
                phq_sum = sum(v for k, v in st.session_state.responses.items() if k.startswith("phq9_"))
                if phq_sum >= 10:
                    st.session_state.phase = "results"
                    st.rerun()
                else:
                    st.rerun()
            else:
                st.warning("Please select an option to continue.")

    elif st.session_state.phase == "results":
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = setup_rag()

        if not st.session_state.scores:
            st.session_state.scores = compute_scores(st.session_state.responses)

        st.subheader("Assessment Scores:")
        for tool, score in st.session_state.scores.items():
            severity = get_severity(score, tool)
            st.write(f"{tool.upper()}: {score} ({severity})")

        if st.button("Generate Reports"):
            parents_text, child_text, parents_pdf, child_pdf = generate_final_conclusion(
                st.session_state.scores, st.session_state.vector_store
            )

            st.subheader("Parents' Report")
            st.markdown(parents_text)
            if parents_pdf:
                st.download_button("Download Parents' PDF", parents_pdf, "parents_report.pdf", "application/pdf")

            st.subheader("Child's Report")
            st.markdown(child_text)
            if child_pdf:
                st.download_button("Download Child's PDF", child_pdf, "child_report.pdf", "application/pdf")



        if st.button("Restart Assessment"):
            for key in ["phase", "welcome_index", "responses", "diagnostic_index", "scores"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()