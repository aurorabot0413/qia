# QiA - QA Inteligente Automatizado

Sistema de automatización de QA con IA para aplicaciones React.

## 🚀 Quick Start

```bash
# Clonar repo
git clone https://github.com/aurorabot0413/qia.git
cd qia

# Configurar environment
cp .env.example .env
# Editar .env con tus credenciales

# Instalar dependencias (orchestrator)
cd orchestrator
pip install -r requirements.txt

# Instalar dependencias (worker)
cd ../worker
pip install -r requirements.txt
playwright install chromium
```

## 📚 Documentación

- [Arquitectura Serverless](docs/ARQUITECTURA_SERVERLESS.md)
- [Plan de Fases](../proyectos/qia/FASES_DESARROLLO.md)
- [Roadmap Completo](../proyectos/qia/ROADMAP.md)

## 🛠️ Tech Stack

- **FastAPI** - Orquestador
- **LangChain** - Framework de agentes
- **Vertex AI Gemini 2.5 Pro** - Análisis de IA
- **Playwright** - Automatización de browser
- **Google Cloud Run** - Serverless hosting
- **Google Cloud Build** - Pipeline efímero

## 👤 Autor

**Aurora Bot** - Aurora Corp

## 📄 Licencia

MIT
