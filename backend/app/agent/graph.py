# backend/app/agent/graph.py

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS
from app.agent.prompts import SYSTEM_PROMPT, INTENT_PROMPT
from app.core.config import settings


# إنشاء الـ LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0.7,
    max_tokens=1000,
)

# ربط الـ tools بالـ LLM
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ══ Nodes ══

def detect_intent(state: AgentState) -> AgentState:
    """تحديد نية المريض من آخر رسالة"""
    messages = state["messages"]
    if not messages:
        return state

    last_message = messages[-1].content
    prompt = INTENT_PROMPT.format(message=last_message)

    response = llm.invoke([HumanMessage(content=prompt)])
    intent = response.content.strip().lower()

    # تأكد إن الـ intent من الخيارات المعروفة
    valid_intents = ["booking", "query", "cancel", "greeting", "other"]
    if intent not in valid_intents:
        intent = "other"

    return {**state, "intent": intent}


def agent_node(state: AgentState) -> AgentState:
    """الـ Node الرئيسي — بيستدعي الـ LLM مع الـ tools"""
    messages = state["messages"]

    # إضافة الـ system prompt
    system_message = SystemMessage(content=SYSTEM_PROMPT)
    all_messages = [system_message] + list(messages)

    response = llm_with_tools.invoke(all_messages)

    return {**state, "messages": [response]}


def should_continue(state: AgentState) -> str:
    """تحديد الخطوة الجاية — هل نستدعي tool ولا ننهي؟"""
    messages = state["messages"]
    last_message = messages[-1]

    # لو الـ LLM طلب tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


# ══ بناء الـ Graph ══

def build_agent_graph():
    graph = StateGraph(AgentState)

    # إضافة الـ nodes
    graph.add_node("detect_intent", detect_intent)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    # تحديد نقطة البداية
    graph.set_entry_point("detect_intent")

    # الـ edges
    graph.add_edge("detect_intent", "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    # بعد الـ tools يرجع للـ agent
    graph.add_edge("tools", "agent")

    return graph.compile()


# Singleton
agent_graph = build_agent_graph()