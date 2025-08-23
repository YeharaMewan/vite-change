from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator

from .tools import all_tools
from .memory_manager import MemoryManager
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from datetime import datetime

# 1. Define the Agent's State
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    session_id: str
    memory_context: list
    user_preferences: dict

# 2. Define the Agent's Logic (The "Thinker" Node)
def agent_node(state: AgentState):
    memory_context = state.get("memory_context", [])

    # Build a simple system prompt that embeds short memory context
    context_snippet = "".join(
        [f"- {m.get('role')}: {m.get('content')[:120]}...\n" for m in memory_context[-3:]]
    )
    system_prompt = (
        "You are a highly intelligent and friendly HR Assistant for a company. "
        "Your primary role is to assist employees with their HR-related inquiries in Sinhala or English.\n"
        "Use the recent conversation context below to maintain continuity.\n\n"
        f"Recent context:\n{context_snippet}\n"
        "Rules: Be concise, choose tools when needed, and keep responses friendly."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    llm_with_tools = llm.bind_tools(all_tools)
    runnable = prompt | llm_with_tools
    response = runnable.invoke({"messages": state["messages"]})

    # persist assistant reply into memory
    try:
        session_id = state.get("session_id", "default")
        MemoryManager().add_message(session_id, "assistant", response.content, {"ts": datetime.now().isoformat()})
    except Exception:
        # avoid breaking the reply if memory write fails
        pass

    return {"messages": [response]}

# 3. Define the Tool Node (The "Actor")
tool_node = ToolNode(all_tools)

# 4. Define the conditional logic to route between nodes
def should_continue(state: AgentState) -> str:
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    return "end_conversation"

llm = ChatOpenAI(model="gpt-4o", temperature=0)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    {"continue_to_tools": "tools", "end_conversation": END}
)
graph.add_edge("tools", "agent")
agent_executor = graph.compile()