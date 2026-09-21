"""
GoodWe EV ChargeOps Agent — Sprint 3
"""

from __future__ import annotations

import time
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq

from config import DEFAULT_MODEL, MODELS, ModelConfig, get_system_prompt
from guardrails import run_input_guard, run_output_guard


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    blocked: bool
    block_reason: str
    model_name: str
    latency_ms: float
    input_tokens: int
    output_tokens: int


def create_llm(config: ModelConfig):
    return ChatGroq(
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def input_guard_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    user_text = last_message.content if hasattr(last_message, "content") else str(last_message)
    block_msg = run_input_guard(user_text)
    if block_msg:
        return {"blocked": True, "block_reason": block_msg, "latency_ms": 0.0, "input_tokens": 0, "output_tokens": 0}
    return {"blocked": False, "block_reason": ""}


def agent_node(state: AgentState) -> dict:
    model_key = state.get("model_name", DEFAULT_MODEL)
    config = MODELS[model_key]
    llm = create_llm(config)
    system_prompt = get_system_prompt()
    messages_for_llm = [SystemMessage(content=system_prompt)] + state["messages"]

    time.sleep(15)
    start = time.time()
    response = llm.invoke(messages_for_llm)
    latency = (time.time() - start) * 1000

    input_text = system_prompt + " ".join(m.content for m in state["messages"] if hasattr(m, "content"))
    input_tokens = len(input_text) // 4
    output_tokens = len(response.content) // 4
    return {"messages": [response], "latency_ms": round(latency, 1), "input_tokens": input_tokens, "output_tokens": output_tokens}


def output_guard_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]
    original = last_msg.content
    filtered = run_output_guard(original)
    if filtered != original:
        return {"messages": [AIMessage(content=filtered)]}
    return {}


def blocked_response_node(state: AgentState) -> dict:
    return {"messages": [AIMessage(content=state["block_reason"])]}


def route_after_guard(state: AgentState) -> str:
    if state.get("blocked", False):
        return "blocked_response"
    return "agent"


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)
    graph.add_node("input_guard", input_guard_node)
    graph.add_node("agent", agent_node)
    graph.add_node("output_guard", output_guard_node)
    graph.add_node("blocked_response", blocked_response_node)
    graph.add_edge(START, "input_guard")
    graph.add_conditional_edges("input_guard", route_after_guard, {"agent": "agent", "blocked_response": "blocked_response"})
    graph.add_edge("agent", "output_guard")
    graph.add_edge("output_guard", END)
    graph.add_edge("blocked_response", END)
    return graph.compile(checkpointer=checkpointer)


class GoodWeAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.memory = MemorySaver()
        self.app = build_graph(checkpointer=self.memory)

    def chat(self, user_message: str, session_id: str = "default") -> dict:
        config = {"configurable": {"thread_id": session_id}}
        result = self.app.invoke(
            {"messages": [HumanMessage(content=user_message)], "model_name": self.model_name,
             "blocked": False, "block_reason": "", "latency_ms": 0.0, "input_tokens": 0, "output_tokens": 0},
            config=config,
        )
        last_ai = result["messages"][-1]
        return {"response": last_ai.content, "latency_ms": result.get("latency_ms", 0.0),
                "input_tokens": result.get("input_tokens", 0), "output_tokens": result.get("output_tokens", 0),
                "blocked": result.get("blocked", False)}

    def reset_session(self, session_id: str = "default"):
        self.memory = MemorySaver()
        self.app = build_graph(checkpointer=self.memory)