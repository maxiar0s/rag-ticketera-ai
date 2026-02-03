import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from app.agent import agent_app  # Importamos nuestro grafo

# --- CONFIGURACIÓN & SEGURIDAD ---
API_KEY_SECRET = os.getenv("RAG_API_KEY", "dev_secret")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY_SECRET:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Credenciales inválidas. Acceso denegado al Cerebro IA."
    )

# --- MODELOS ---
class TicketRequest(BaseModel):
    subject: str
    content: str

# --- CICLO DE VIDA (DB) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Aquí irá la conexión real a Postgres (pgvector)
    # Por ahora lo mantenemos limpio para probar el grafo
    print("🚀 Iniciando Microservicio AI...")
    yield
    print("🛑 Apagando...")

app = FastAPI(title="Ticketera AI Agent", lifespan=lifespan)

# --- ENDPOINTS ---
@app.post("/agent/process", dependencies=[Depends(verify_api_key)])
async def process_ticket(ticket: TicketRequest):
    """
    Endpoint principal que invoca a LangGraph.
    """
    # Invocamos el grafo
    inputs = {
        "ticket_subject": ticket.subject,
        "ticket_content": ticket.content,
        "retrieved_docs": [],
        "final_response": "",
        "category": ""
    }
    
    # LangGraph ejecuta el flujo
    result = await agent_app.ainvoke(inputs)
    
    return {
        "status": "success",
        "category": result["category"],
        "solution": result["final_response"],
        "sources": result["retrieved_docs"]
    }