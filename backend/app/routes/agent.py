from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Literal

from app.database import get_db
from app.ai_assistant import answer_question
from app.neo4j_service import sync_graph, verify_connectivity
from app.auth import get_current_user, require_role
from app import models

router = APIRouter(prefix="/agent", tags=["LangChain Agent"])


class AgentQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list["AgentMessage"] = Field(default_factory=list, max_length=10)


class AgentMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


AgentQuestion.model_rebuild()


@router.post("/ask")
def ask_agent(
    request: AgentQuestion,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    result = answer_question(
        request.question,
        db,
        [message.model_dump() for message in request.history],
        current_user,
    )

    return {
        "question": request.question,
        **result,
    }


@router.get("/status")
def agent_status(
    current_user: models.User = Depends(require_role(["admin"]))
):
    import os

    return {
        "neo4j": verify_connectivity(),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "framework": "LangChain",
        "tools": [
            "search_products",
            "get_product",
            "get_inventory_status",
            "get_orders",
            "get_order",
            "get_vendors",
            "get_purchase_orders",
            "get_fulfillment_report",
            "get_business_snapshot",
            "search_product_knowledge",
            "get_user_preferences",
            "save_user_preference",
            "get_recommendations",
            "track_order",
            "get_analytics_insights",
            "compare_marketplace_offers",
            "queue_support_email",
        ],
        "architecture": {
            "planner": "compiled LangGraph workflow",
            "specialists": ["shopping", "product", "pricing", "inventory", "order", "recommendation", "knowledge", "analytics"],
            "memory": "persistent SQL user memory",
            "rag": "product document retrieval",
            "knowledge_graph": "Neo4j optional",
            "mcp": "working local demo gateway; optional live providers",
        },
    }


@router.post("/sync")
def sync_agent_graph(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role(["admin"]))
):
    return {"synced": True, "counts": sync_graph(db)}
