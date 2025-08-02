# Child Mental Health Assessment Bot

This project is a Streamlit-based AI-powered chatbot that interactively assesses mental health (with a focus on depression) in children and adolescents. It uses a structured questionnaire, rule-based logic for question flow, and an LLM-powered report generation for conclusions.

---

## Project Structure

* `question_pool.py` — Contains the list of diagnostic questions with options and scoring.
* `scoring_guide.py` — Defines scoring thresholds and severity levels for different mental health scales.
* `welcome_questions.py` — Contains the warm-up welcome questions to engage the user.
* `child_mental_rag.py` — Main Streamlit app implementing the questionnaire flow and final report generation.

---

## Prerequisites

* Python 3.8 or higher
* Recommended: Create a Python virtual environment for project isolation

### Install Required Packages

```bash
pip install streamlit openai python-docx reportlab langchain faiss-cpu
```

* `streamlit` — For the web app UI
* `openai` — To call OpenAI API for report generation
* `python-docx` — To parse any .docx files if needed
* `reportlab` — For generating PDF reports (if used)
* `langchain` and `faiss-cpu` — For RAG (Retrieval-Augmented Generation) setup with vector search

---

## Setup OpenAI API Key

The app requires an OpenAI API key to generate the final mental health assessment report.

1. Obtain your API key from [OpenAI](https://platform.openai.com/account/api-keys).
2. Set the environment variable:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

On Windows PowerShell:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Alternatively, create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

---

## Running the App

1. Ensure all the files (`question_pool.py`, `scoring_guide.py`, `welcome_questions.py`, `child_mental_rag.py`) are in the same directory.

2. Run the Streamlit app:

```bash
streamlit run child_mental_rag.py
```

3. This will open the app in your default web browser or give a local URL like `http://localhost:8501`.

---

## Usage

* The app starts by asking **welcome questions** to engage the child.
* Then it transitions to **diagnostic questions** related to depression and mental health.
* Once the questions complete or a threshold is met, it computes scores.
* Press **Generate Report** to get a personalized, empathetic summary for the child and parents.
* You can restart the assessment anytime with the **Restart Assessment** button.

---

## Notes

* The question flow uses **sequential rule-based logic** without AI-driven adaptive questioning to minimize costs and complexity.
* The report generation **uses OpenAI's GPT model** with Retrieval-Augmented Generation (RAG) for contextualized summaries.
* The scoring and severity thresholds are based on validated clinical scales included in `scoring_guide.py`.
* Ensure your OpenAI API key has sufficient quota to avoid rate limits.
* The app stores user responses only in session state and does not persist data externally.

---

## Troubleshooting

* **OpenAI API Errors:**
  Check your API key setup and internet connection.

* **Streamlit UI Issues:**
  Clear browser cache or restart Streamlit server.

* **Module Import Errors:**
  Confirm all required packages are installed in the active environment.

---

## Contribution & Customization

* You can extend `question_pool.py` to add or modify diagnostic questions.
* Adjust thresholds or add new scoring scales in `scoring_guide.py`.
* Modify welcome questions in `welcome_questions.py` for better engagement.
* Customize `child_mental_rag.py` for UI or logic changes.

---

If you need further assistance or want the repo structure and scripts refactored, just ask!

