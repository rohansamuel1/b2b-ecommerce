"""Real LangGraph orchestration for transparent ecommerce task decomposition."""
from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END


class CommerceState(TypedDict, total=False):
    question: str
    role: str
    plan: list[dict[str, str]]
    specialists: list[str]
    execution: list[dict[str, str]]


RULES = [
    ("order_agent", ["order", "shipment", "tracking", "arrive", "refund", "return"]),
    ("inventory_agent", ["stock", "inventory", "available", "availability"]),
    ("pricing_agent", ["price", "budget", "under", "coupon", "discount", "cheapest", "compare"]),
    ("recommendation_agent", ["recommend", "similar", "accessor", "complete", "setup", "best"]),
    ("knowledge_agent", ["manual", "warranty", "compatible", "specification", "troubleshoot", "policy"]),
    ("analytics_agent", ["revenue", "analytics", "trend", "kpi", "highest", "performance"]),
    ("product_agent", ["product", "find", "search", "brand", "category"]),
]


def _plan(state: CommerceState) -> CommerceState:
    text = state["question"].lower()
    specialists = [name for name, words in RULES if any(word in text for word in words)] or ["shopping_agent"]
    return {"specialists": specialists, "plan": [{"agent": name, "task": f"Resolve the {name.replace('_', ' ')} portion"} for name in specialists]}


def _execute(state: CommerceState) -> CommerceState:
    return {"execution": [{"agent": name, "status": "ready", "scope": state.get("role", "anonymous")} for name in state["specialists"]]}


builder = StateGraph(CommerceState)
builder.add_node("planner", _plan)
builder.add_node("specialists", _execute)
builder.add_edge(START, "planner")
builder.add_edge("planner", "specialists")
builder.add_edge("specialists", END)
commerce_workflow = builder.compile()


def run_workflow(question: str, role: str = "anonymous") -> dict[str, Any]:
    result = commerce_workflow.invoke({"question": question, "role": role})
    return {"engine": "LangGraph", "specialists": result["specialists"], "steps": result["plan"], "execution": result["execution"], "complex": len(result["specialists"]) > 1}
