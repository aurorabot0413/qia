"""
Cloud Build Trigger - Dispara pipelines de QA
"""
from google.cloud import cloudbuild_v1
from google.cloud import storage
import logging
from typing import Optional
import json

from core.config import settings

logger = logging.getLogger(__name__)


class CloudBuildTrigger:
    """Maneja la ejecución de pipelines en Cloud Build"""
    
    def __init__(self):
        self.client = cloudbuild_v1.CloudBuildClient()
        self.storage_client = storage.Client()
    
    async def run_qa_pipeline(self, repo_name: str, pr_number: int):
        """
        Dispara el pipeline de QA en Cloud Build
        
        Args:
            repo_name: Nombre del repositorio (ej: "owner/repo")
            pr_number: Número del Pull Request
        """
        try:
            # Generar cloudbuild.yaml dinámico
            build_config = self._generate_build_config(repo_name, pr_number)
            
            # Subir cloudbuild.yaml a GCS
            build_file_url = await self._upload_build_config(build_config, pr_number)
            
            # Crear y ejecutar build
            build = cloudbuild_v1.Build(
                source=cloudbuild_v1.Source(
                    storage_source=cloudbuild_v1.StorageSource(
                        bucket=settings.BUCKET_NAME,
                        object_=f"builds/pr-{pr_number}-cloudbuild.yaml"
                    )
                ),
                steps=build_config["steps"],
                substitutions={
                    "_REPO_NAME": repo_name,
                    "_PR_NUMBER": str(pr_number),
                    "_GEMINI_MODEL": settings.GEMINI_MODEL
                }
            )
            
            # Ejecutar
            operation = self.client.create_build(
                project_id=settings.PROJECT_ID,
                build=build
            )
            
            logger.info(f"Build started for PR #{pr_number}: {operation.metadata.build.id}")
            
            return operation.metadata.build.id
            
        except Exception as e:
            logger.error(f"Error triggering QA pipeline: {e}")
            raise
    
    def _generate_build_config(self, repo_name: str, pr_number: int) -> dict:
        """Genera la configuración del build dinámicamente"""
        return {
            "steps": [
                # Paso 1: Clonar repo
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": [
                        "clone",
                        f"https://github.com/{repo_name}.git",
                        "."
                    ]
                },
                # Paso 2: Checkout PR branch
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": [
                        "fetch",
                        "origin",
                        f"pull/{pr_number}/head:pr-{pr_number}"
                    ]
                },
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": ["checkout", f"pr-{pr_number}"]
                },
                # Paso 3: Build Docker imagen app
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["build", "-t", "app-react", "."]
                },
                # Paso 4: Levantar app (detached)
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": [
                        "run",
                        "-d",
                        "-p", "3000:3000",
                        "--name", "app",
                        "app-react"
                    ]
                },
                # Paso 5: Ejecutar QA Worker
                {
                    "name": "gcr.io/$PROJECT_ID/qia-worker",
                    "args": [],
                    "env": [
                        f"APP_URL=http://localhost:3000",
                        f"PR_NUMBER={pr_number}",
                        f"REPO_NAME={repo_name}",
                        f"GEMINI_MODEL={settings.GEMINI_MODEL}"
                    ]
                },
                # Paso 6: Cleanup
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["rm", "-f", "app"]
                }
            ],
            "timeout": "1200s",
            "options": {
                "machineType": "N1_HIGHCPU_8"
            }
        }
    
    async def _upload_build_config(self, config: dict, pr_number: int) -> str:
        """Sube el archivo de configuración a GCS"""
        bucket = self.storage_client.bucket(settings.BUCKET_NAME)
        blob = bucket.blob(f"builds/pr-{pr_number}-cloudbuild.yaml")
        
        import yaml
        blob.upload_from_string(yaml.dump(config))
        
        return f"gs://{settings.BUCKET_NAME}/builds/pr-{pr_number}-cloudbuild.yaml"
