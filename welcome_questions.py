# welcome_questions.py
# ------------------------------------------------------------
# Non-scored intake items shown before the adaptive assessment.
# Keep these lightweight and unambiguous. The main app stores
# answers in session state; these IDs intentionally do NOT match
# any scored instrument prefixes (phq9_, gad7_, etc.).
#
# Types supported by the current UI:
#   - "radio": uses q["options"]
#   - "text" : free text (required by current UI flow)
# ------------------------------------------------------------

from typing import List, Dict, Any

welcome_questions: List[Dict[str, Any]] = [
    {
        "id": "welcome_ack",
        "type": "radio",
        "text": (
            "This tool is a screening aid, not a diagnosis or emergency service. "
            "If you or the child are in immediate danger, contact local emergency services. "
            "Do you understand and want to continue?"
        ),
        "options": ["Yes, I understand and want to continue", "No"],
    },
    {
        "id": "welcome_role",
        "type": "radio",
        "text": "Who is completing this assessment?",
        "options": ["Child (age 8–17)", "Parent or caregiver", "Other adult"],
    },
    {
        "id": "welcome_age_band",
        "type": "radio",
        "text": "What is the age of the child being assessed?",
        "options": ["8–10", "11–13", "14–17"],
    },
    {
        "id": "welcome_language",
        "type": "radio",
        "text": "Preferred language for questions:",
        "options": ["English", "हिन्दी (Hindi)", "ಕನ್ನಡ (Kannada)"],
    },
    {
        "id": "welcome_privacy",
        "type": "radio",
        "text": "Are you in a private space where you feel comfortable answering honestly?",
        "options": ["Yes", "Mostly", "No"],
    },
    {
        "id": "welcome_guardian_consent",
        "type": "radio",
        "text": (
            "If you are a parent/caregiver, do you consent to the child participating in this screening?"
        ),
        "options": ["Yes", "No", "Not applicable"],
    },
    {
        "id": "welcome_risk_gate",
        "type": "radio",
        "text": (
            "Right now, are you (or the child) in immediate danger or having thoughts of self-harm? "
            "If yes, please seek urgent help first via local emergency services before continuing."
        ),
        "options": ["No, we can continue", "Yes, I need help now"],
    },
    {
        "id": "welcome_name",
        "type": "text",
        "text": "What name should we use to address you during this assessment?",
        # no options for text; current UI treats text as required
    },
]
