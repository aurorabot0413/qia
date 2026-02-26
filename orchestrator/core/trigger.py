"""
Cloud Build Trigger - Dispara pipelines de QA
"""
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


class CloudBuildTrigger:
    """Maneja la ejecución de pipelines en Cloud Build"""
    
    def __init__(self):
        self._client = None
        self._storage_client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from google.cloud import cloudbuild_v1
                self._client = cloudbuild_v1.CloudBuildClient()
            except Exception as e:
                logger.error(f"Failed to create CloudBuild client: {e}")
                raise
        return self._client
    
    @property
    def storage_client(self):
        if self._storage_client is None:
            try:
                from google.cloud import storage
                self._storage_client = storage.Client()
            except Exception as e:
                logger.error(f"Failed to create Storage client: {e}")
                raise
        return self._storage_client
    
    @property
    def bucket_name(self):
        return os.getenv("BUCKET_NAME", "qia-artifacts-bucket")
    
    @property
    def project_id(self):
        return os.getenv("PROJECT_ID", "core-trees-487719-n8")
    
    @property
    def gemini_model(self):
        return os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    
    async def run_qa_pipeline(self, repo_name: str, pr_number: int):
        """
        Dispara el pipeline de QA en Cloud Build
        """
        try:
            import yaml
            from google.cloud import cloudbuild_v1
            
            # Generar cloudbuild.yaml dinámico
            build_config = self._generate_build_config(repo_name, pr_number)
            
            # Subir cloudbuild.yaml a GCS
            build_file_url = await self._upload_build_config(build_config, pr_number)
            
            # Crear y ejecutar build
            build = cloudbuild_v1.Build(
                source=cloudbuild_v1.Source(
                    storage_source=cloudbuild_v1.StorageSource(
                        bucket=self.bucket_name,
                        object_=f"builds/pr-{pr_number}-cloudbuild.yaml"
                    )
                ),
                steps=build_config["steps"],
                substitutions={
                    "_REPO_NAME": repo_name,
                    "_PR_NUMBER": str(pr_number),
                    "_GEMINI_MODEL": self.gemini_model
                }
            )
            
            # Ejecutar
            operation = self.client.create_build(
                project_id=self.project_id,
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
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": ["clone", f"https://github.com/{repo_name}.git", "."]
                },
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": ["fetch", "origin", f"pull/{pr_number}/head:pr-{pr_number}"]
                },
                {
                    "name": "gcr.io/cloud-builders/git",
                    "args": ["checkout", f"pr-{pr_number}"]
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["build", "-t", "app-react", "."]
                },
                {
                    "name": "gcr.io/cloud-builders/docker",
                    "args": ["run", "-d", "-p", "3000:3000", "--name", "app", "app-react"]
                },
                {
                    "name": f"gcr.io/{self.project_id}/qia-worker",
                    "env": [
                        f"APP_URL=http://localhost:3000",
                        f"PR_NUMBER={pr_number}",
                        f"REPO_NAME={repo_name}",
                        f"GEMINI_MODEL={self.gemini_model}"
                    ]
                },
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
        import yaml
        
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"builds/pr-{pr_number}-cloudbuild.yaml")
        
        blob.upload_from_string(yaml.dump(config))
        
        return f"gs://{self.bucket_name}/builds/pr-{pr_number}-cloudbuild.yaml"
