import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.utils.tools import consultar_mis_tickets

# Configuración centralizada del modelo
llm_base = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", # Ajusta a la versión válida que tengas disponible
    temperature=0,
    google_api_key=os.environ.get("GOOGLE_API_KEY")
)

llm = llm_base.bind_tools([consultar_mis_tickets])