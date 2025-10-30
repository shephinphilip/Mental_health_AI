#pip install pyautogen -q autogen

# ============================================================
#  Multi-Agent Clinical Report Generator (AutoGen version)
# ============================================================

from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import os, json
from datetime import datetime

# Load session
SESSION_PATH = "/content/chat_sessions/session_20251030_065740.json" #conversation history file path
with open(SESSION_PATH, "r", encoding="utf-8") as f:
    convo = json.load(f)

conversation_text = "\n".join(
    [f"You: {t.get('user','')}\nAI: {t.get('ai','')}" for t in convo]
)

# Define base LLM config
llm_config = {
    "model": "gpt-4o-mini",
    "api_key": os.getenv("OPENAI_API_KEY"),
    "temperature": 0.7,
}

# Agent definitions
therapist_agent = AssistantAgent(
    name="TherapistAgent",
    llm_config=llm_config,
    system_message=(
        "Empathetic therapist that summarizes conversations in reflective, "
        "clinical language without diagnostic terms. Use gentle humor, validation, and care."
    ),
)

closure_agent = AssistantAgent(
    name="ClosureAgent",
    llm_config=llm_config,
    system_message=(
        "Closure specialist creating unsent emotional letters for healing. "
        "Each section should have a clear header (e.g., 'To Father', 'To Self')."
    ),
)

routine_agent = AssistantAgent(
    name="RoutinePlannerAgent",
    llm_config=llm_config,
    system_message=(
        "Routine planner that builds a 7-day recovery plan blending self-care, reflection, "
        "social connection, and creative activities."
    ),
)

# Orchestrator to manage message passing
manager = GroupChatManager(
    groupchat=GroupChat(
        agents=[therapist_agent, closure_agent, routine_agent],
        messages=[],
        max_round=3
    ),
    llm_config=llm_config,
)

# User proxy initiates the chat
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    system_message="Provide the conversation text and request the full report.",
    llm_config=llm_config,
)

prompt = f"Here is the conversation:\n{conversation_text}\n\nGenerate a clinical-style summary, closure letters, and a 7-day recovery routine."

user_proxy.initiate_chat(manager, message=prompt)

# Save outputs
report_path = f"/content/chat_sessions/report_autogen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(manager.groupchat.messages, f, ensure_ascii=False, indent=2)

print(f"✅ Multi-agent AutoGen report saved at: {report_path}")
