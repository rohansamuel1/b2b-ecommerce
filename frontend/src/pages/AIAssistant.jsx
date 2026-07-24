import { useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  BrainCircuit,
  Database,
  PackageSearch,
  Send,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import API from "../api/api";
import { getStoredUser } from "../auth";

const suggestedPrompts = [
  "Give me a business snapshot for the marketplace.",
  "Which products are low stock right now?",
  "Show recent orders and fulfillment status.",
  "Which vendors and purchase orders need attention?",
];

function AIAssistant() {
  const user = getStoredUser();
  const isAdmin = user?.role === "admin";
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState("");
  const messagesEndRef = useRef(null);

  const history = useMemo(() => messages.slice(-10).map((message) => ({
    role: message.sender === "assistant" ? "assistant" : "user",
    content: message.text,
  })), [messages]);

  useEffect(() => {
    if (!isAdmin) return;

    API.get("/agent/status")
      .then((response) => setStatus(response.data))
      .catch((error) => {
        console.error(error);
        setStatusError("Assistant status is unavailable.");
      });
  }, [isAdmin]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const askAgent = async (event, promptOverride) => {
    event?.preventDefault();
    const userQuestion = (promptOverride || question).trim();

    if (!userQuestion || loading) return;

    setQuestion("");
    setLoading(true);
    setMessages((prev) => [...prev, { sender: "user", text: userQuestion }]);

    try {
      const response = await API.post("/agent/ask", {
        question: userQuestion,
        history,
      });

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: response.data.answer,
          meta: {
            source: response.data.source,
            model: response.data.model,
            tools: response.data.tools,
            graphError: response.data.graph_error,
            plan: response.data.plan,
          },
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          text: error.response?.data?.detail || "Something went wrong while contacting the LangChain assistant.",
          meta: { source: "error" },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="assistant-page">
      <div className="assistant-header">
        <div>
          <span className="eyebrow">LangChain workspace</span>
          <h1>AI Assistant</h1>
          <p>
            Ask about products, inventory, orders, vendors, purchase orders, fulfillment,
            and operational KPIs. The assistant uses tools and only returns data your role can access.
          </p>
        </div>

        <div className="assistant-status-card">
          <div className="assistant-status-title">
            <BrainCircuit size={18} aria-hidden="true" />
            Agent Status
          </div>
          <div className="assistant-status-grid">
            <span><Sparkles size={14} aria-hidden="true" /> {status?.framework || "LangChain"}</span>
            <span><Workflow size={14} aria-hidden="true" /> {status?.tools?.length || 15} tools</span>
            <span><Bot size={14} aria-hidden="true" /> {status?.openai_configured ? status.model : "local fallback"}</span>
            <span><Database size={14} aria-hidden="true" /> {status?.neo4j?.connected ? "Neo4j connected" : "Neo4j optional"}</span>
            <span><Workflow size={14} aria-hidden="true" /> {status?.github_mcp?.connected ? "GitHub MCP connected" : "GitHub MCP optional"}</span>
          </div>
          {statusError && <p className="assistant-status-error">{statusError}</p>}
        </div>
      </div>

      <section className="assistant-suggestions" aria-label="Suggested prompts">
        {suggestedPrompts.map((prompt) => (
          <button
            key={prompt}
            className="assistant-prompt"
            type="button"
            onClick={(event) => askAgent(event, prompt)}
            disabled={loading}
          >
            <PackageSearch size={16} aria-hidden="true" />
            <span>{prompt}</span>
          </button>
        ))}
      </section>

      <section className="assistant-chat" aria-live="polite">
        {messages.length === 0 && (
          <div className="assistant-empty">
            <ShieldCheck size={28} aria-hidden="true" />
            <h2>Ready for commerce questions</h2>
            <p>
              Try a snapshot, low-stock report, order lookup, vendor summary, or fulfillment analysis.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={`${message.sender}-${index}`}
            className={`assistant-message assistant-message-${message.sender}`}
          >
            <div className="assistant-bubble">
              <div className="assistant-bubble-label">
                {message.sender === "user" ? user?.name || "You" : "LangChain Assistant"}
              </div>
              <div className="assistant-bubble-text">{message.text}</div>
              {message.meta && (
                <div className="assistant-meta">
                  {message.meta.source && <span>{message.meta.source}</span>}
                  {message.meta.model && <span>{message.meta.model}</span>}
                  {message.meta.tools ? <span>{message.meta.tools} tools</span> : null}
                  {message.meta.graphError && <span>Graph note: {message.meta.graphError}</span>}
                  {message.meta.plan?.specialists?.length ? <span>Agents: {message.meta.plan.specialists.join(", ")}</span> : null}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="assistant-message assistant-message-assistant">
            <div className="assistant-bubble">
              <div className="assistant-bubble-label">LangChain Assistant</div>
              <div className="assistant-thinking">Choosing tools and checking commerce data...</div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </section>

      <form className="assistant-composer" onSubmit={askAgent}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about orders, inventory, vendors, purchase orders, or KPIs..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()} aria-label="Send question">
          <Send size={18} aria-hidden="true" />
          <span>{loading ? "Thinking" : "Ask"}</span>
        </button>
      </form>
    </div>
  );
}

export default AIAssistant;
