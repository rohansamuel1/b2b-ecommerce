"""Grounded assistant that combines LangChain tools with optional Neo4j retrieval."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app import models
from app.langchain_agent import run_langchain_agent, simple_order_agent, route_specialists
from app.neo4j_service import is_configured, retrieve_context, sync_graph

load_dotenv()


def _context_fallback(question: str, context: dict, db: Session, current_user: models.User | None) -> str:
    if not context:
        return simple_order_agent(question, db, current_user)
    return (
        "I found the following matching commerce data in Neo4j. "
        "Configure OPENAI_API_KEY for a conversational summary.\n\n"
        + json.dumps(context, indent=2, default=str)
    )


def answer_question(
    question: str,
    db: Session,
    history: list[dict] | None = None,
    current_user: models.User | None = None,
) -> dict:
    context: dict = {}
    graph_used = False
    graph_error = None

    if is_configured():
        try:
            if os.getenv("NEO4J_SYNC_ON_ASK", "true").lower() == "true":
                sync_graph(db)
            context = retrieve_context(question, current_user)
            graph_used = True
        except Exception as exc:
            graph_error = str(exc)

    if os.getenv("OPENAI_API_KEY"):
        try:
            agent_result = run_langchain_agent(
                question,
                db,
                history or [],
                current_user,
                context,
            )
            return {
                "answer": agent_result["answer"],
                "source": "langchain+neo4j" if graph_used else "langchain",
                "graph_error": graph_error,
                "model": agent_result["model"],
                "tools": agent_result["tool_count"],
                "plan": agent_result["plan"],
            }
        except Exception as exc:
            graph_error = graph_error or f"LangChain: {exc}"

    return {
        "answer": _context_fallback(question, context, db, current_user),
        "source": "neo4j" if graph_used else "local",
        "graph_error": graph_error,
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini") if os.getenv("OPENAI_API_KEY") else None,
        "tools": 0,
        "system": "langchain-fallback",
        "plan": route_specialists(question, current_user.role if current_user else "anonymous"),
    }
