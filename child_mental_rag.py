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

# Load environment variables
load_dotenv()
# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)

# Document content (from provided document)


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

def get_critical_question(responses: Dict[str, int]) -> Optional[Dict]:
    critical_ids = ["phq9_9", "kads_7", "rcads_dep_9", "dass_dep_7", "cesd_9"]
    for qid in critical_ids:
        if qid not in responses:
            return next((q for q in question_pool if q["id"] == qid), None)
    return None

def get_next_question(responses: Dict[str, int]) -> Optional[Dict]:
    """Use OpenAI to select the next question based on responses."""
    if not responses:
        # Start with a broad depression question
        return next((q for q in question_pool if q["id"] == "phq9_1"), None)

    # Prepare response summary (anonymized to avoid PII)
    question_lookup = {q["id"]: q for q in question_pool}
    response_summary = "\n".join([
        f"Q: {question_lookup[qid]['category']} question (ID: {qid})\nA: Score {score}/{question_lookup[qid]['score_range'][-1]}"
        for qid, score in responses.items() if qid in question_lookup
    ])

    # List unanswered questions
    available_questions = [
        f"ID: {q['id']}, Category: {q['category']}, Text: {q['text']}"
        for q in question_pool if q["id"] not in responses
    ]

    # Construct prompt for OpenAI
    prompt = f"""
You are a mental health assessment assistant. Below is a summary of answered questions from a mental health questionnaire, anonymized to protect privacy. Based on the responses, select the next most relevant question from the available questions that has not been answered. Prioritize questions that help narrow down to a primary diagnostic category (depression, anxiety, bipolar, OCD, PTSD) and assess severity or critical risks (e.g., self-harm). Return only the ID of the next question.

Answered questions:
{response_summary}

Available questions:
{available_questions}

Return: ID of the next question to ask.
"""
    response = call_openai(prompt)
    try:
        # Extract question ID (assuming model outputs "ID: <qid>")
        next_qid = response.split("ID: ")[-1].strip().split("\n")[0]
        return next((q for q in question_pool if q["id"] == next_qid), None)
    except:
        # Fallback to a random unanswered question
        return next((q for q in question_pool if q["id"] not in responses), None)

def compute_scores(responses: Dict[str, int]) -> Dict[str, int]:
    scores = {
        "phq9": 0,
        "kads11": 0,
        "rcads_depression": 0,
        "dass21_depression": 0,
        "cesd": 0,
        "mfq_sf": 0
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
            scores["mfq_sf"] += score
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
        # Ask diagnostic questions sequentially, no LLM-based adaptive logic
        if st.session_state.diagnostic_index < len(question_pool) and st.session_state.diagnostic_index < MAX_DIAGNOSTIC_QUESTIONS:
            q = question_pool[st.session_state.diagnostic_index]

            st.write(f"Question {st.session_state.diagnostic_index + 1}: {q['text']}")

            answer = st.radio("Select an option:", q["options"], key=f"diag_{q['id']}")

            if st.button("Next", key=f"diag_next_{q['id']}"):
                if answer in q["options"]:
                    answer_index = q["options"].index(answer)
                    score = q["score_range"][answer_index]
                    st.session_state.responses[q["id"]] = score
                    st.session_state.diagnostic_index += 1

                    # Optionally: check if depression threshold crossed early to finish early
                    scores = compute_scores(st.session_state.responses)
                    # Example threshold: PHQ9 >= 10 means probable depression
                    if scores.get("phq9", 0) >= 10:
                        st.session_state.phase = "results"
                        st.rerun()
                    else:
                        st.rerun()
                else:
                    st.warning("Please select an option to continue.")
        else:
            # Max questions reached, move to results
            st.session_state.phase = "results"
            st.rerun()

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