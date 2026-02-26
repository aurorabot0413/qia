"""
QiA Orchestrator - FastAPI App
"""
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import os

app = FastAPI(
    title="QiA Orchestrator",
    description="QA Inteligente Automatizado",
    version="0.1.0"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/")
async def root():
    return {
        "service": "QiA Orchestrator", 
        "status": "running",
        "project": os.getenv("PROJECT_ID", "unknown"),
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Recibe webhooks de GitHub (PR opened/updated)
    Dispara Cloud Build para ejecutar QA
    """
    try:
        payload = await request.json()
        
        # Validar que es un PR
        if payload.get("pull_request"):
            pr_number = payload["pull_request"]["number"]
            repo_name = payload["repository"]["full_name"]
            action = payload.get("action")
            
            logger.info(f"PR #{pr_number} - Action: {action} - Repo: {repo_name}")
            
            # Disparar Cloud Build en background
            background_tasks.add_task(
                trigger_qa_pipeline,
                repo_name=repo_name,
                pr_number=pr_number
            )
            
            return JSONResponse(
                status_code=202,
                content={
                    "status": "accepted",
                    "message": f"QA pipeline triggered for PR #{pr_number}"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={"status": "ignored", "message": "Not a PR event"}
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


async def trigger_qa_pipeline(repo_name: str, pr_number: int):
    """Dispara el pipeline de QA en Cloud Build"""
    try:
        from core.trigger import CloudBuildTrigger
        trigger = CloudBuildTrigger()
        await trigger.run_qa_pipeline(repo_name, pr_number)
        logger.info(f"QA pipeline triggered for PR #{pr_number}")
    except Exception as e:
        logger.error(f"Error in QA pipeline: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
