"""
Pub/Sub Webhook Simulator
Para testing local sin necesidad de GitHub webhooks reales
"""
import json
from datetime import datetime
from google.cloud import pubsub_v1
import logging

logger = logging.getLogger(__name__)


class WebhookSimulator:
    """Simula webhooks de GitHub usando Pub/Sub"""
    
    def __init__(self, project_id: str, topic_name: str = "qia-webhooks"):
        self.project_id = project_id
        self.topic_name = topic_name
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
    
    def simulate_pr_opened(self, repo_name: str, pr_number: int):
        """
        Simula webhook de PR abierto
        
        Args:
            repo_name: Nombre del repo (ej: "aurorabot0413/qia-test-app")
            pr_number: Número del PR
        """
        payload = {
            "action": "opened",
            "pull_request": {
                "number": pr_number,
                "title": f"Test PR #{pr_number}",
                "body": "This is a test PR for QiA",
                "state": "open",
                "user": {
                    "login": "aurorabot0413"
                },
                "base": {
                    "ref": "main"
                },
                "head": {
                    "ref": f"feature/test-{pr_number}"
                },
                "additions": 10,
                "deletions": 5,
                "changed_files": 2
            },
            "repository": {
                "full_name": repo_name,
                "name": repo_name.split("/")[1],
                "owner": {
                    "login": repo_name.split("/")[0]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        self._publish(payload)
        logger.info(f"Simulated PR #{pr_number} opened for {repo_name}")
    
    def simulate_pr_updated(self, repo_name: str, pr_number: int):
        """Simula webhook de PR actualizado"""
        payload = {
            "action": "synchronize",
            "pull_request": {
                "number": pr_number,
                "title": f"Test PR #{pr_number} (updated)",
                "state": "open"
            },
            "repository": {
                "full_name": repo_name
            }
        }
        
        self._publish(payload)
        logger.info(f"Simulated PR #{pr_number} updated for {repo_name}")
    
    def _publish(self, payload: dict):
        """Publica mensaje en Pub/Sub"""
        try:
            # Crear tema si no existe
            try:
                self.publisher.create_topic(request={"name": self.topic_path})
                logger.info(f"Topic created: {self.topic_path}")
            except Exception as e:
                # Topic ya existe
                pass
            
            # Publicar mensaje
            data = json.dumps(payload).encode("utf-8")
            future = self.publisher.publish(self.topic_path, data)
            
            message_id = future.result()
            logger.info(f"Published message {message_id} to {self.topic_path}")
            
        except Exception as e:
            logger.error(f"Error publishing to Pub/Sub: {e}")
            raise


if __name__ == "__main__":
    # Ejemplo de uso
    import os
    
    simulator = WebhookSimulator(
        project_id=os.getenv("PROJECT_ID", "core-trees-487719-n8")
    )
    
    # Simular PR abierto
    simulator.simulate_pr_opened(
        repo_name="aurorabot0413/qia-test-app",
        pr_number=1
    )
    
    print("Webhook simulado publicado en Pub/Sub")
