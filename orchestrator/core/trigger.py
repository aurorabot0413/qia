"""
Cloud Build Trigger - Dispara pipelines de QA
"""
import logging
import os
import json

logger = logging.getLogger(__name__)


class CloudBuildTrigger:
    """Maneja la ejecución de pipelines de QA en Cloud Build"""
    
    def __init__(self):
        self._client = None
        self._storage_client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from google.cloud.devtools import cloudbuild_v1
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
            from google.cloud.devtools import cloudbuild_v1
            from google.protobuf import duration_pb2
            
            # Generar pasos del build
            steps = self._generate_build_steps(repo_name, pr_number)
            
            # Crear build con steps directos (sin source, el primer step clona)
            build = {
                "steps": steps,
                "substitutions": {
                    "_REPO_NAME": repo_name,
                    "_PR_NUMBER": str(pr_number),
                    "_GEMINI_MODEL": self.gemini_model,
                    "_PROJECT_ID": self.project_id,
                    "_BUCKET_NAME": self.bucket_name
                },
                "timeout": "1200s",
                "options": {
                    "machineType": "N1_HIGHCPU_8"
                }
            }
            
            # Subir config a GCS y ejecutar
            config_yaml = await self._upload_build_config(build, pr_number)
            
            # Crear build desde GCS
            build_obj = cloudbuild_v1.Build(
                source=cloudbuild_v1.Source(
                    storage_source=cloudbuild_v1.StorageSource(
                        bucket=self.bucket_name,
                        object_=f"builds/pr-{pr_number}-cloudbuild.yaml"
                    )
                ),
                steps=steps,
                substitutions=build["substitutions"],
                timeout=duration_pb2.Duration(seconds=1200)
            )
            
            # Ejecutar
            operation = self.client.create_build(
                project_id=self.project_id,
                build=build_obj
            )
            
            build_id = operation.metadata.build.id if operation.metadata else "pending"
            logger.info(f"Build started for PR #{pr_number}: {build_id}")
            
            return build_id
            
        except Exception as e:
            logger.error(f"Error triggering QA pipeline: {e}")
            raise
    
    async def _upload_build_config(self, config: dict, pr_number: int) -> str:
        """Sube el archivo de configuración a GCS"""
        import yaml
        
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(f"builds/pr-{pr_number}-cloudbuild.yaml")
        blob.upload_from_string(yaml.dump(config))
        
        return f"gs://{self.bucket_name}/builds/pr-{pr_number}-cloudbuild.yaml"
    
    def _generate_build_steps(self, repo_name: str, pr_number: int) -> list:
        """Genera los pasos del build para QA"""
        project_id = self.project_id
        
        return [
            # Paso 1: Clonar repo
            {
                "name": "gcr.io/cloud-builders/git",
                "id": "clone",
                "args": ["clone", f"https://github.com/{repo_name}.git", "."]
            },
            # Paso 2: Checkout del PR
            {
                "name": "gcr.io/cloud-builders/git",
                "id": "checkout-pr",
                "entrypoint": "bash",
                "args": ["-c", f"git fetch origin pull/{pr_number}/head:pr-{pr_number} && git checkout pr-{pr_number}"]
            },
            # Paso 3: Detectar y buildear
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "build-app",
                "entrypoint": "bash",
                "args": ["-c", """
                    if [ -f Dockerfile ]; then
                        docker build -t app-to-test .
                    elif [ -f package.json ]; then
                        npm ci --legacy-peer-deps 2>/dev/null || npm install
                        npm run build
                        echo 'FROM nginx:alpine
                        COPY build /usr/share/nginx/html
                        EXPOSE 8080' > Dockerfile.temp
                        docker build -f Dockerfile.temp -t app-to-test .
                    else
                        echo "No build system detected, using dummy"
                        echo 'FROM nginx:alpine' > Dockerfile.dummy
                        docker build -f Dockerfile.dummy -t app-to-test .
                    fi
                """]
            },
            # Paso 4: Levantar app
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "run-app",
                "entrypoint": "bash",
                "args": ["-c", """
                    docker run -d --name test-app -p 3000:8080 app-to-test || true
                    sleep 5
                """]
            },
            # Paso 5: QA Worker
            {
                "name": f"gcr.io/{project_id}/qia-worker",
                "id": "qa-worker",
                "env": [
                    "APP_URL=http://localhost:3000",
                    f"PR_NUMBER={pr_number}",
                    f"REPO_NAME={repo_name}",
                    f"GEMINI_MODEL={self.gemini_model}",
                    f"PROJECT_ID={project_id}",
                    f"BUCKET_NAME={self.bucket_name}"
                ]
            },
            # Paso 6: Cleanup
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "cleanup",
                "entrypoint": "bash",
                "args": ["-c", "docker rm -f test-app || true"]
            }
        ]
