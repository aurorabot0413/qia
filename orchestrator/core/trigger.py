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
        
        El pipeline:
        1. Clona el repo y hace checkout del PR
        2. Detecta el tipo de proyecto
        3. Build de la app
        4. Ejecuta el QA Worker
        5. Genera y sube reporte
        """
        try:
            from google.cloud import cloudbuild_v1
            
            # Crear build con source directo del repo
            build = cloudbuild_v1.Build(
                source=cloudbuild_v1.Source(
                    repo_source=cloudbuild_v1.RepoSource(
                        repo_name=f"github_{repo_name.replace('/', '_')}",
                        branch_name=f"pr-{pr_number}",
                        # Alternativamente usar pull_request
                    )
                ),
                steps=self._generate_build_steps(repo_name, pr_number),
                substitutions={
                    "_REPO_NAME": repo_name,
                    "_PR_NUMBER": str(pr_number),
                    "_GEMINI_MODEL": self.gemini_model,
                    "_PROJECT_ID": self.project_id,
                    "_BUCKET_NAME": self.bucket_name
                },
                timeout="1200s",
                options=cloudbuild_v1.BuildOptions(
                    machine_type="N1_HIGHCPU_8",
                    logging="CLOUD_LOGGING_ONLY"
                )
            )
            
            # Ejecutar build
            operation = self.client.create_build(
                project_id=self.project_id,
                build=build
            )
            
            build_id = operation.metadata.build.id if operation.metadata else "unknown"
            logger.info(f"Build started for PR #{pr_number}: {build_id}")
            
            return build_id
            
        except Exception as e:
            logger.error(f"Error triggering QA pipeline: {e}")
            # Fallback: usar storage source
            return await self._run_with_storage_source(repo_name, pr_number)
    
    async def _run_with_storage_source(self, repo_name: str, pr_number: int) -> str:
        """Fallback: crear build config y subirlo a GCS"""
        try:
            import yaml
            from google.cloud import cloudbuild_v1
            
            # Generar cloudbuild.yaml
            build_config = {
                "steps": self._generate_build_steps(repo_name, pr_number),
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
            
            # Subir a GCS
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(f"builds/pr-{pr_number}-cloudbuild.yaml")
            blob.upload_from_string(yaml.dump(build_config))
            
            # Crear build
            build = cloudbuild_v1.Build(
                source=cloudbuild_v1.Source(
                    storage_source=cloudbuild_v1.StorageSource(
                        bucket=self.bucket_name,
                        object_=f"builds/pr-{pr_number}-cloudbuild.yaml"
                    )
                ),
                steps=build_config["steps"],
                substitutions=build_config["substitutions"]
            )
            
            operation = self.client.create_build(
                project_id=self.project_id,
                build=build
            )
            
            build_id = operation.metadata.build.id if operation.metadata else "unknown"
            return build_id
            
        except Exception as e:
            logger.error(f"Error in fallback build: {e}")
            raise
    
    def _generate_build_steps(self, repo_name: str, pr_number: int) -> list:
        """Genera los pasos del build para QA"""
        project_id = self.project_id
        
        return [
            # Paso 1: Clonar repo
            {
                "name": "gcr.io/cloud-builders/git",
                "id": "clone",
                "args": [
                    "clone",
                    f"https://github.com/{repo_name}.git",
                    "."
                ]
            },
            # Paso 2: Fetch y checkout del PR
            {
                "name": "gcr.io/cloud-builders/git",
                "id": "checkout-pr",
                "args": [
                    "fetch", "origin",
                    f"pull/{pr_number}/head:pr-{pr_number}",
                    "&&",
                    "git", "checkout", f"pr-{pr_number}"
                ],
                "entrypoint": "bash",
                "args": ["-c", f"git fetch origin pull/{pr_number}/head:pr-{pr_number} && git checkout pr-{pr_number}"]
            },
            # Paso 3: Detectar tipo de proyecto y hacer build
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "build-app",
                "entrypoint": "bash",
                "args": ["-c", """
                    if [ -f Dockerfile ]; then
                        docker build -t app-to-test .
                    elif [ -f package.json ]; then
                        # Node.js app
                        npm ci --legacy-peer-deps
                        npm run build
                        # Crear Docker image temporal
                        echo 'FROM nginx:alpine
COPY build /usr/share/nginx/html
EXPOSE 8080' > Dockerfile.temp
                        docker build -f Dockerfile.temp -t app-to-test .
                    else
                        echo "No build system detected"
                        exit 1
                    fi
                """]
            },
            # Paso 4: Levantar app en background
            {
                "name": "gcr.io/cloud-builders/docker",
                "id": "run-app",
                "entrypoint": "bash",
                "args": ["-c", """
                    docker run -d --name test-app -p 3000:8080 app-to-test
                    sleep 5
                    curl -f http://localhost:3000/ || echo "App may not have root endpoint"
                """]
            },
            # Paso 5: Ejecutar QA Worker
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
                "args": ["rm", "-f", "test-app"],
                "entrypoint": "bash",
                "args": ["-c", "docker rm -f test-app || true"]
            }
        ]
