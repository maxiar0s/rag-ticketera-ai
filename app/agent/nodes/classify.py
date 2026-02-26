from langchain_core.messages import HumanMessage

from app.agent.state import AgentState


def determine_query_complexity(query: str, docs_count: int) -> str:
    normalized = (query or "").strip().lower()

    if not normalized:
        return "low"

    low_signals = (
        "hola",
        "gracias",
        "adios",
        "ok",
        "si",
        "no",
        "buenos dias",
        "buenas tardes",
    )
    if len(normalized) <= 45 and any(normalized.startswith(signal) for signal in low_signals):
        return "low"

    high_signals = (
        "arquitectura",
        "plan",
        "estrategia",
        "compar",
        "analiza",
        "debug",
        "error",
        "stack",
        "migr",
        "paso a paso",
        "integr",
        "implement",
        "optim",
        "consulta sql",
        "script",
        "automat",
    )

    if len(normalized) > 260:
        return "high"
    if docs_count >= 6:
        return "high"
    if any(signal in normalized for signal in high_signals):
        return "high"

    if len(normalized) <= 80 and docs_count <= 2:
        return "low"

    return "medium"


def classify_node(state: AgentState):
    print("--- 🧭 NODE: CLASSIFY ---", flush=True)

    last_human_message = ""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            last_human_message = message.content
            break

    complexity_tier = determine_query_complexity(
        query=last_human_message,
        docs_count=len(state.get("documents", [])),
    )

    print(f"💸 Complexity tier detectado: {complexity_tier}", flush=True)
    return {"complexity_tier": complexity_tier}
