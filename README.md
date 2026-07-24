# AI B2B Ecommerce Platform

This repository implements the architecture in **AI Ecommerce Agent Roadmap - Final Architecture** as a working, locally runnable application. It combines a normal multi-vendor commerce system with grounded AI tools, persistent preference memory, product-document RAG, Neo4j graph context, hybrid recommendations, specialist-agent routing, order support, analytics, and optional MCP-style integrations.

## Architecture

`React -> FastAPI -> SQLAlchemy -> SQLite/PostgreSQL`

The AI request path is:

`User question -> specialist planner -> LangChain tool agent -> scoped commerce/RAG/memory/graph tools -> response`

SQLite remains the zero-configuration local default. PostgreSQL, Redis, and Neo4j are included in `docker-compose.yml` for the production-shaped deployment. External LLM and MCP services are optional and credential-gated.

## Roadmap coverage

| Phase | Implementation |
| --- | --- |
| 1 - Ecommerce backend | JWT auth, role controls, categories, catalog search/filtering, cart, wishlist, orders, reviews, coupons, inventory, vendors, purchase orders, invoices |
| 2 - First AI agent | LangChain tool-calling assistant backed by live SQL data |
| 3 - RAG | Product manuals, specifications, warranties, FAQs, policies, local vector retrieval, knowledge-base admin UI |
| 4 - Memory | Chat history plus persistent user preference memory with user controls |
| 5 - Knowledge graph | Neo4j projection, fixed parameterized Cypher retrieval, product/vendor/order relationships |
| 6 - Multi-agent | Transparent planner routes to shopping, product, pricing, inventory, order, recommendation, knowledge, and analytics specialists |
| 7 - MCP | Admin-visible connector registry and safe environment switches for filesystem, GitHub, search, fetch, browser, database, and email adapters |
| 8 - Recommendations | Hybrid scoring across purchase categories, wishlist, preferences, ratings, and availability |
| 9 - Planning | Multi-intent decomposition is included in every AI response as an execution plan |
| 10 - Order assistant | Shipment tracking, delay next-actions, return requests, fulfillment logs, invoice support |
| 11 - Analytics agent | Category revenue, product revenue, order status, return activity, charts, and an admin analytics tool |
| 12 - Production platform | React/FastAPI containers, PostgreSQL, Redis service, Neo4j, environment configuration, tests and graceful fallbacks |

## Run locally

Backend:

```bash
cd backend
cp .env.example .env
venv/bin/pip install -r requirements.txt
venv/bin/uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The default API URL is `http://127.0.0.1:8000`; interactive API docs are at `/docs`.

## Run the production-shaped stack

```bash
docker compose up --build
```

Change all demo passwords and secrets before exposing this stack. Add `OPENAI_API_KEY` and the desired `OPENAI_MODEL` to the backend environment for LLM responses. Without it, the app retains local deterministic fallback behavior.

## Verification

```bash
cd backend && PYTHONPATH=. venv/bin/python -m unittest discover -s tests -v
cd frontend && npm run lint && npm run build
```

## Important integration boundary

MCP entries represent supported adapter boundaries and are disabled by default. Enabling a flag reports the connector as configured, but a real third-party MCP server, its transport, credentials, allowlist, and operational policy must be supplied by the deployment owner. The application never fabricates access to Amazon reviews, Slack, email, GitHub, maps, or external search services.
