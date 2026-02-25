# Arquitectura de QiA

## 🏗️ Componentes

### 1. **Orquestador (Cloud Run - FastAPI)**
- Recibe webhooks de GitHub
- Dispara Cloud Build
- No ejecuta Docker directamente

### 2. **Ejecutor (Cloud Build)**
- Clona repositorio
- Construye imagen Docker de app React
- Levanta contenedor efímero
- Ejecuta QA-Worker

### 3. **QA-Worker (LangChain + Vertex AI)**
- Analiza PR (GitHub API)
- Navega automáticamente con Playwright
- Captura screenshots
- **LangChain Agent** con Vertex AI Gemini 2.5 Pro
- Genera reportes

### 4. **Persistencia (Cloud Storage)**
- Screenshots
- Reportes HTML/JSON

---

## 🤖 LangChain + Vertex AI

### Configuración del Agente

```python
from langchain_google_vertexai import VertexAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool

# Modelo Gemini 2.5 Pro
llm = VertexAI(
    model_name="gemini-2.5-pro",
    temperature=0.1,
    max_output_tokens=8192
)

# Herramientas del agente
tools = [
    Tool(
        name="analyze_screenshot",
        func=analyze_screenshot,
        description="Analiza screenshots visuales"
    ),
    Tool(
        name="review_code",
        func=review_code,
        description="Revisa código en busca de bugs"
    ),
    Tool(
        name="check_accessibility",
        func=check_accessibility,
        description="Verifica accesibilidad"
    )
]

# Agente
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
```

### Prompt del Sistema

```
Eres un QA Senior especializado en aplicaciones React.

Tus herramientas:
- analyze_screenshot: Analiza screenshots visuales
- review_code: Revisa código en busca de bugs
- check_accessibility: Verifica accesibilidad

Tu trabajo:
1. Analizar el PR
2. Detectar errores visuales
3. Revisar código
4. Verificar accesibilidad
5. Generar reporte

Formato de salida:
{
  "status": "approved|rejected|needs_review",
  "confidence": 0.95,
  "issues": [...],
  "summary": "..."
}
```

---

## 💰 Costos

| Servicio | Costo/mes |
|----------|-----------|
| Cloud Run | $0-5 |
| Cloud Build | $0-10 |
| Vertex AI (Gemini 2.5 Pro) | $10-30 |
| Cloud Storage | $0.20 |
| **TOTAL** | **$10-45** |

**Cubierto por créditos de Google** ✅

---

## 🔐 Seguridad

- API Keys en Secret Manager
- Variables de entorno inyectadas
- Sin hardcodear credenciales
