# ===== Mental Health Assessment Tool for Adolescents =====
# This app presents an on-screen questionnaire for adolescents and their caregivers.
# It has three phases:
#   (1) WELCOME (non-scored intake & consent)
#   (2) DIAGNOSTIC (adaptive question selection WITHOUT using AI models)
#   (3) RESULTS (scores + optional narrative reports)
#
# IMPORTANT:
# - The code that decides what diagnostic question to ask next (the "engine") is
#   100% deterministic and rule-based. It DOES NOT use any AI/LLM.
# - Language models are only used later to help draft human-readable reports
#   from public guidance content (RAG). If you need a model-free app entirely,
#   you can remove the RAG/report parts without touching the selection engine.

import os
from typing import Dict, List, Optional, Tuple
import logging
import openai  # used ONLY for report drafting (NOT for question selection)
import streamlit as st
from io import BytesIO
import time
from openai import OpenAI
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from docx import Document

# These are your local data files:
from depression_question_pool import question_pool     # all scored items
from depression_scoring_guide import scoring_guides    # score → severity mapping
from welcome_questions import welcome_questions        # non-scored intake
from dotenv import load_dotenv
from functools import lru_cache
from collections import defaultdict

# ===== System Configuration and Setup =====

# Load API keys etc. from a .env file (keeps secrets out of source code)
load_dotenv()

# OpenAI is used ONLY to generate narrative reports (optional). The question
# selection engine does NOT use OpenAI or any other model.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== Critical Safety Assessment Questions =====
# These are ALWAYS asked first (if not already asked), because they screen for
# immediate safety concerns. If any are unanswered, the engine serves them
# before anything else.
CRITICAL_IDS = {
    "phq9_9",   # suicidal ideation
    "kads_7",   # suicide/self-harm thoughts/actions
    "cesd_9"    # life failure / self-destructive feeling
}

# ===== Per-Category Minimum Coverage Targets =====
# The engine tries to ensure we have enough evidence in each area before finishing.
# This keeps the assessment balanced and not overly focused on one topic.
CATEGORY_TARGETS = {
    "depression": 9,   # PHQ-9 items (typical minimum for screening)
    "anxiety": 7,      # GAD-7 core
    "ptsd": 8,         # short PCL-5 coverage
    "ocd": 10,         # OCI-R coverage
    "bipolar": 7,      # MDQ core
}

# ===== "Core" Instruments Per Category =====
# We mildly prefer questions from these instruments because they are widely
# used and well-validated. This does NOT force the engine to choose only these,
# it simply nudges toward them when useful.
CORE_ANCHORS = {
    "depression": {"phq9", "kads11", "cesd", "mfqsf", "dass21"},
    "anxiety":    {"gad7", "hads", "scared", "scas", "rcads", "dass21", "dassy"},
    "ptsd":       {"pcl5", "iesr"},
    "ocd":        {"oci_r", "ybocs"},
    "bipolar":    {"mdq", "bsds"},
}

# ===== Weights for the Deterministic Selection Engine =====
# These are simple "knobs" that explain how the engine makes trade-offs:
#   - W_NEED:    prefer categories we haven't covered enough yet
#   - W_CORE:    prefer recognized/validated questionnaires (above)
#   - W_NOVELTY: avoid repeating the same instrument too many times in a row
#   - W_DISCRIM: when evidence is unclear, prefer questions that help
#                distinguish between top competing categories
W_NEED    = 2.0
W_CORE    = 1.0
W_NOVELTY = 0.3
W_DISCRIM = 0.7


# ===== Helper: load external guidance text for reports =====
def load_document_content(filename: str) -> str:
    """Read a .docx and return its text as one long string."""
    doc = Document(filename)
    return "\n".join([para.text for para in doc.paragraphs])


DOCUMENT_CONTENT = load_document_content("AI_Training_Document.docx")

# ===== Logging (errors, warnings) =====
logging.basicConfig(
    filename="openai_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===== Vector store for RAG (report drafting only; optional) =====
@st.cache_resource
def setup_rag():
    """
    Build a small local search index over your guidance document to help the
    report generator cite relevant advice. This does NOT affect question selection.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=lambda text: len(text)
    )
    documents = text_splitter.create_documents([DOCUMENT_CONTENT])
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store


# ===== OpenAI wrapper (only used for report generation) =====
def call_openai(prompt: str) -> str:
    """
    Call OpenAI with robust error handling. This is NOT used by the question
    selection engine. It is only used later to turn structured results into
    narrative summaries for parents and kids.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        # Clean any previous error flags
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


# ======== DETERMINISTIC QUESTION SELECTION ENGINE (NO LLM) ========

def _instrument_key(qid: str, q: dict) -> str:
    """
    Identify which questionnaire ("instrument") a question belongs to.
    This helps the engine vary question sources (PHQ-9 vs CES-D, etc.).
    """
    inst = (q.get("instrument") or "").strip().lower()
    if inst:
        return inst.replace(" ", "_").replace("-", "").replace("/", "_")
    ql = qid.lower()
    for fam in [
        "phq9","kads","gad7","hads","hama","scas","scared","rcads","pcl5","iesr",
        "oci_r","ybocs","mdq","bsds","dass21","dassy","y_psc","ypsc","pdss","lsas"
    ]:
        if ql.startswith(fam):
            return fam
    return "misc"


@lru_cache(maxsize=1)
def _id_to_item() -> Dict[str, dict]:
    """Fast lookup table from question id → question object."""
    return {q["id"]: q for q in question_pool}


def _max_per_item(q: dict) -> int:
    """The highest possible score for a single question (used as tiny tie-breaker)."""
    sr = q.get("score_range") or []
    return max(sr) if sr else 0


def _normalized_answer(qid: str, raw_score: int) -> float:
    """
    Convert an answer to a 0..1 scale so different instruments can be compared fairly.
    e.g., if an item is 0..3 and the user picks 2, we record 2/3 ≈ 0.67.
    """
    q = _id_to_item().get(qid)
    if not q:
        return 0.0
    m = _max_per_item(q)
    return (raw_score / m) if m > 0 else 0.0


def _category_stats(responses: Dict[str, int]):
    """
    Summarize what we know so far from answered questions:

    - mean severity (0..1) per category: how "high" the answers are on average
    - coverage per category: how many items asked vs. a suggested minimum target
    - counts per instrument: to avoid long streaks from the same questionnaire
    - asked_ids: which question ids we already asked (to avoid repeats)
    """
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

    mean = {c: (by_cat_sum[c] / by_cat_cnt[c]) if by_cat_cnt[c] else 0.0 for c in by_cat_cnt}
    cov  = {c: (by_cat_cnt[c] / CATEGORY_TARGETS.get(c, 6)) for c in by_cat_cnt}
    return asked_ids, mean, cov, by_inst_cnt


def _top_two_categories(mean: Dict[str, float]) -> Tuple[Optional[str], Optional[str], float]:
    """
    Identify the top two categories by average severity and how far apart they are.
    If the top two are close, we are "uncertain" and should ask questions that
    help tell them apart.
    """
    if not mean:
        return None, None, 1.0
    ranked = sorted(mean.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[0][0]
    second = ranked[1][0] if len(ranked) > 1 else None
    margin = (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else ranked[0][1]
    return top, second, margin


def get_critical_question(responses: Dict[str, int]) -> Optional[Dict]:
    """
    RULE 1: Safety first. If any critical item is unanswered, ask it immediately.
    """
    asked = set(responses.keys())
    for qid in CRITICAL_IDS:
        if qid not in asked and qid in _id_to_item():
            return _id_to_item()[qid]
    return None


def get_next_question(responses: Dict[str, int]) -> Optional[Dict]:
    """
    MAIN ENGINE: Pick the next best question to ask, using transparent rules:

    Step 1) Critical items first (suicidality, self-harm).
    Step 2) Compute what we know so far:
            - How severe each category looks (0..1 average)
            - How many questions we’ve asked in each category (coverage)
            - Which instrument we used last (to add variety)
            - Whether the top two categories are close (uncertainty)
    Step 3) For each candidate (unasked) question, compute a simple score:
            utility = W_NEED*(1 - coverage) + W_CORE*(core bonus) +
                      W_NOVELTY*(switch instrument) + W_DISCRIM*(helps disambiguate)
            Add a tiny tie-breaker for questions with more scoring granularity.
    Step 4) Pick the question with the highest utility.

    This produces explainable behavior that does NOT rely on any machine learning.
    """
    # — Step 1: critical items get priority —
    crit = get_critical_question(responses)
    if crit:
        return crit

    # — Step 2: summarize answered items —
    asked_ids, mean, cov, by_inst_cnt = _category_stats(responses)
    top, second, margin = _top_two_categories(mean)

    # If the top two categories are very close, we are "uncertain" and give a
    # small preference to questions from those categories to tell them apart.
    uncertain = (margin < 0.20) if (top and second) else True

    # Track the instrument used most recently so we can vary sources a bit
    last_inst = None
    if responses:
        # Because dicts preserve insertion order in Python 3.7+, the "last" key is the
        # most recently answered item.
        last_qid = next(reversed(responses.keys()))
        last_q = _id_to_item().get(last_qid)
        if last_q:
            last_inst = _instrument_key(last_qid, last_q)

    # — Step 3: evaluate all remaining candidates —
    best_q = None
    best_u = float("-inf")

    for q in question_pool:
        qid = q["id"]
        if qid in asked_ids:
            continue  # skip questions we've already asked

        cat = q["category"]
        inst = _instrument_key(qid, q)

        # Need term: prefer categories we haven't covered enough yet (0..1)
        cat_cov = cov.get(cat, 0.0)
        need_term = (1.0 - min(1.0, cat_cov))

        # Core instruments get a small bonus (validity preference)
        core_set = CORE_ANCHORS.get(cat, set())
        core_bonus = 1.0 if any(inst.startswith(k) for k in core_set) else 0.0

        # Novelty: a small nudge to switch instruments so the experience feels varied
        novelty = 1.0 if (last_inst and inst != last_inst) else 0.0

        # Discrimination: when uncertain, favor top-2 categories; otherwise deepen the top
        if uncertain:
            discrim = 1.0 if (cat == top or cat == second) else 0.0
        else:
            discrim = 1.0 if (cat == top) else 0.0

        # Utility = weighted sum of the above. Transparent and adjustable.
        utility = (W_NEED * need_term) + (W_CORE * core_bonus) + (W_NOVELTY * novelty) + (W_DISCRIM * discrim)

        # Tiny tie-breaker: prefer questions with a larger max score (slightly finer resolution)
        utility += 0.01 * _max_per_item(q)

        # If tied, choose lexicographically smaller id for stability
        if utility > best_u or (utility == best_u and qid < (best_q["id"] if best_q else "")):
            best_q, best_u = q, utility

    # None means we’ve asked everything or there are no candidates left
    return best_q


# ===== Scoring (sum raw scores per instrument family) =====
def compute_scores(responses: Dict[str, int]) -> Dict[str, int]:
    """
    Turn raw answers into instrument totals.
    NOTE: This function focuses on depression instruments (as per original file).
    Add more families here if you want system-wide totals for anxiety/PTSD/OCD, etc.
    """
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
            # It’s OK if many items are not part of these sums (e.g., anxiety/PTSD/OCD items)
            logging.debug(f"Ignoring non-depression id in depression totals: {qid}")

    # DASS-21 convention: multiply subscale sum by 2 before interpretation
    scores["dass21_depression"] *= 2
    return scores


def get_severity(score: int, tool: str) -> str:
    """
    Map a raw total score to a human-readable severity band using scoring_guides.
    If a tool (like RCADS) needs T-scores, we return a friendly note.
    """
    if tool in ["rcads_depression", "rcads_anxiety"]:
        return "Not applicable (requires T-score conversion)"
    if tool not in scoring_guides:
        return "Unknown"
    for min_score, max_score, severity in scoring_guides[tool]["thresholds"]:
        if min_score <= score <= max_score:
            return severity
    return "Unknown"


# ===== Report Generation (optional; uses RAG + OpenAI for prose only) =====
def generate_final_conclusion(scores: Dict[str, int], vector_store) -> Tuple[str, str, bytes, bytes]:
    """
    Build two narrative reports (Parents + Child). This step:
      1) summarizes critical items,
      2) infers a primary category in a simple way,
      3) retrieves guidance text (RAG) to ground recommendations,
      4) asks an LLM to draft readable text.
    If you need a 100% model-free system, skip calling this and present only scores.
    """
    if vector_store is None:
        return "Error: Vector store not initialized.", "", None, None

    # (1) Summarize answers to a few critical items for the report
    critical_summary = {
        "phq9_9": f"{st.session_state.responses.get('phq9_9', 'Not answered')}/3",
        "kads_9": f"{st.session_state.responses.get('kads_9', 'Not answered')}/2",
        "rcads_dep_9": f"{st.session_state.responses.get('rcads_dep_9', 'Not answered')}/3",
        "dass_dep_7": f"{st.session_state.responses.get('dass_dep_7', 'Not answered')}/3",
        "cesd_9": f"{st.session_state.responses.get('cesd_9', 'Not answered')}/3",
    }

    # (2) Roughly pick a “primary” category to frame guidance.
    #     (Here we look at the depression-related totals only; extend as needed.)
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

    # (3) Retrieve guidance text related to {primary_category} and {severity}
    query = f"Guidelines for supporting adolescents with {primary_category} at {severity} severity."
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)

    # (4) Ask the LLM to draft two separate sections (parents + child)
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

    # Split the two sections by the marker we asked the model to use
    if "--- Child's Report ---" in full_text:
        parents_text, child_text = full_text.split("--- Child's Report ---", 1)
        parents_text = parents_text.replace("--- Parents' Report ---", "").strip()
        child_text = child_text.strip()
    else:
        parents_text, child_text = full_text, ""

    # Render PDFs (simple black-on-white pages with paragraphs)
    def create_pdf(content: str) -> bytes:
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


# ===== Streamlit UI =====
def main():
    st.title("Adolescent Mental Health Assessment")

    # --- API Key Setup ---
    if "api_key" not in st.session_state:
        st.session_state.api_key = None

    if not st.session_state.api_key:
        api_key_input = st.text_input(
            "Enter your OpenAI API key",
            type="password",
            placeholder="sk-...",
        )
        if st.button("Save API Key"):
            if api_key_input.startswith("sk-"):
                st.session_state.api_key = api_key_input
                st.success("API Key saved! You can now proceed.")
                st.rerun()
            else:
                st.error("Please enter a valid OpenAI API key (starts with sk-).")
        return  # stop execution until API key is provided

    # Override client with user-provided key
    global client
    client = OpenAI(api_key=st.session_state.api_key)

    # --- Configurable number of diagnostic questions ---
    if "max_diag_qs" not in st.session_state:
        st.session_state.max_diag_qs = 15  # default

    st.sidebar.header("Settings")
    st.session_state.max_diag_qs = st.sidebar.selectbox(
        "Maximum Diagnostic Questions",
        options=[5, 10, 15, 20, 25, 30],
        index=2  # default = 15
    )

    # --- Session state initialization ---
    if "phase" not in st.session_state:
        st.session_state.phase = "welcome"
    if "welcome_index" not in st.session_state:
        st.session_state.welcome_index = 0
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "diagnostic_index" not in st.session_state:
        st.session_state.diagnostic_index = 0
    if "scores" not in st.session_state:
        st.session_state.scores = None

    # ----- Phase 1: Welcome / Intake (non-scored) -----
    if st.session_state.phase == "welcome":
        q = welcome_questions[st.session_state.welcome_index]
        st.write(q["text"])

        if q["type"] == "text":
            answer = st.text_input("Your answer:", key=f"welcome_{q['id']}")
        elif q["type"] == "radio":
            answer = st.radio("Select one:", q["options"], key=f"welcome_{q['id']}")
        else:
            answer = None

        if st.button("Next", key=f"welcome_next_{q['id']}"):
            # We simply store these answers; they do NOT affect scoring directly.
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

    # ----- Phase 2: Diagnostic (adaptive, deterministic) -----
    elif st.session_state.phase == "diagnostic":
        # Count how many diagnostic (scored) items we've already collected
        diag_answered = len([k for k in st.session_state.responses if k in _id_to_item()])

        # Stop if we hit the cap
        if diag_answered >= st.session_state.max_diag_qs:
            st.session_state.phase = "results"
            st.rerun()

        # Ask the next best question
        next_q = get_next_question(st.session_state.responses)

        # If no question is available, proceed to results
        if next_q is None:
            st.session_state.phase = "results"
            st.rerun()

        st.write(f"Question {diag_answered + 1}: {next_q['text']}")
        ans = st.radio("Select an option:", next_q["options"], key=f"diag_{next_q['id']}")

        if st.button("Next", key=f"diag_next_{next_q['id']}"):
            if ans in next_q["options"]:
                idx = next_q["options"].index(ans)
                raw_score = next_q["score_range"][idx]
                st.session_state.responses[next_q["id"]] = raw_score

                # OPTIONAL EARLY EXIT:
                # If depression looks clearly moderate+ early, you could finish sooner.
                phq_sum = sum(v for k, v in st.session_state.responses.items() if k.startswith("phq9_"))
                if phq_sum >= 10:
                    st.session_state.phase = "results"
                    st.rerun()
                else:
                    st.rerun()
            else:
                st.warning("Please select an option to continue.")

    # ----- Phase 3: Results -----
    elif st.session_state.phase == "results":
        # Build the vector store only if we’ll generate narrative reports
        if "vector_store" not in st.session_state:
            st.session_state.vector_store = setup_rag()

        if not st.session_state.scores:
            st.session_state.scores = compute_scores(st.session_state.responses)

        st.subheader("Assessment Scores:")
        for tool, score in st.session_state.scores.items():
            severity = get_severity(score, tool)
            st.write(f"{tool.upper()}: {score} ({severity})")

        # Optional: Generate PDFs with parent & child-friendly narratives
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

        # Restart the whole flow
        if st.button("Restart Assessment"):
            for key in ["phase", "welcome_index", "responses", "diagnostic_index", "scores"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()