# B2B ecommerce backend

The complete project setup and roadmap coverage are documented in the repository root `README.md`.

## AI assistant with Neo4j

The assistant projects the relational commerce data into Neo4j and retrieves
relevant graph facts with fixed, parameterized Cypher queries. The OpenAI
Responses API turns those facts into a conversational answer. SQLite remains
the source of truth.

1. Create a Neo4j database locally or in Neo4j Aura.
2. Copy the Neo4j and OpenAI settings from `.env.example` into `.env`.
3. Install dependencies with `venv/bin/pip install -r requirements.txt`.
4. Start the API, sign in as an admin, and open **AI Assistant**.

`POST /agent/sync` forces a graph refresh. By default, `/agent/ask` also syncs
before retrieval so answers reflect current transactional data. Set
`NEO4J_SYNC_ON_ASK=false` for larger deployments and call the sync endpoint
from a job instead.

`GET /agent/status` reports whether Neo4j is connected and whether an OpenAI
key is configured; it never returns credentials.

Use a dedicated Neo4j database/user for this application. The sync deletes
only nodes tagged with `source: "b2b-ecommerce"`, but a dedicated database
provides the cleanest operational boundary.
