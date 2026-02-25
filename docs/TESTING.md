# QiA - Local Testing Guide

## 🧪 Testing Local

### 1. **Orquestador (FastAPI)**

```bash
cd orchestrator

# Crear venv
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Correr servidor
uvicorn main:app --reload --port 8080
```

**Probar endpoints:**
```bash
# Health check
curl http://localhost:8080/

# Webhook (simulado)
curl -X POST http://localhost:8080/webhook/github \
  -H "Content-Type: application/json" \
  -d '{
    "action": "opened",
    "pull_request": {
      "number": 1,
      "title": "Test PR"
    },
    "repository": {
      "full_name": "aurorabot0413/qia-test-app"
    }
  }'
```

---

### 2. **QA Worker**

```bash
cd worker

# Crear venv
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar Playwright browsers
playwright install chromium

# Configurar variables de entorno
export APP_URL="http://localhost:3000"
export GITHUB_TOKEN="tu_token"
export PR_NUMBER=1
export REPO_NAME="aurorabot0413/qia-test-app"

# Correr worker
python qa_script.py
```

---

### 3. **App de Prueba (React)**

```bash
cd ../qia-test-app

# Instalar dependencias
npm install

# Correr app
npm start

# En otra terminal, construir Docker
docker build -t qia-test-app .
docker run -p 3000:3000 qia-test-app
```

---

### 4. **Simular Webhooks con Pub/Sub**

```bash
# En orchestrator/
python webhook_simulator.py
```

---

## 🧪 Testing en Cloud

### 1. **Deploy a Cloud Run**

```bash
# Build y push
gcloud builds submit --tag gcr.io/PROJECT_ID/qia-orchestrator

# Deploy
gcloud run deploy qia-orchestrator \
  --image gcr.io/PROJECT_ID/qia-orchestrator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=PROJECT_ID
```

### 2. **Configurar Pub/Sub**

```bash
# Crear tema
gcloud pubsub topics create qia-webhooks

# Crear suscripción
gcloud pubsub subscriptions create qia-webhooks-sub \
  --topic=qia-webhooks \
  --push-endpoint=https://qia-orchestrator-XXXXX.run.app/webhook/github
```

---

## ✅ Checklist de Testing

- [ ] Orquestador corre en localhost:8080
- [ ] Endpoint /health responde 200
- [ ] Endpoint /webhook acepta payload de GitHub
- [ ] Worker captura screenshots
- [ ] Worker genera reporte HTML
- [ ] Reporte se sube a Cloud Storage
- [ ] Pub/Sub simula webhooks
- [ ] Cloud Build ejecuta pipeline
- [ ] Cloud Run sirve la API

---

## 🐛 Debugging

**Logs del orquestador:**
```bash
gcloud run logs read --service=qia-orchestrator
```

**Logs de Cloud Build:**
```bash
gcloud builds log BUILD_ID
```

**Logs del worker:**
```bash
# Ver en Cloud Build logs
```

---

## 📊 Métricas

**Ver métricas en Cloud Console:**
- Cloud Run → qia-orchestrator → Metrics
- Cloud Build → History
- Pub/Sub → qia-webhooks → Metrics
