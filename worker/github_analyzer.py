"""
GitHub PR Analyzer
"""
from github import Github
import logging
from typing import Dict, List
import os

logger = logging.getLogger(__name__)


class GitHubPRAnalyzer:
    """Analiza Pull Requests de GitHub"""
    
    def __init__(self):
        self.github = Github(os.getenv("GITHUB_TOKEN"))
    
    async def analyze_pr(self, repo_name: str, pr_number: int) -> Dict:
        """
        Analiza un Pull Request
        
        Args:
            repo_name: Nombre del repo (ej: "owner/repo")
            pr_number: Número del PR
        
        Returns:
            Dict con información del PR
        """
        try:
            # Obtener repo y PR
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Obtener archivos modificados
            modified_files = []
            for file in pr.get_files():
                modified_files.append({
                    "filename": file.filename,
                    "status": file.status,  # added, modified, removed
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "raw_url": file.raw_url
                })
            
            # Inferir rutas modificadas
            modified_routes = self._infer_routes(modified_files)
            
            # Obtener cambios en el código
            code_changes = []
            for file in pr.get_files():
                if file.filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    code_changes.append({
                        "filename": file.filename,
                        "patch": file.patch
                    })
            
            pr_data = {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "modified_files": modified_files,
                "modified_routes": modified_routes,
                "code_changes": code_changes,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files
            }
            
            logger.info(f"PR #{pr_number} analyzed: {len(modified_files)} files modified")
            
            return pr_data
            
        except Exception as e:
            logger.error(f"Error analyzing PR #{pr_number}: {e}")
            raise
    
    def _infer_routes(self, modified_files: List[Dict]) -> List[str]:
        """
        Infiere las rutas de la app basándose en los archivos modificados
        
        Args:
            modified_files: Lista de archivos modificados
        
        Returns:
            Lista de rutas (ej: ["/login", "/dashboard"])
        """
        routes = set()
        
        for file in modified_files:
            filename = file["filename"]
            
            # Detectar componentes
            if "components" in filename or "pages" in filename or "views" in filename:
                # Extraer nombre del componente
                name = filename.split("/")[-1].replace(".js", "").replace(".jsx", "")
                name = name.replace(".ts", "").replace(".tsx", "")
                
                # Convertir a ruta
                if "Login" in name or "login" in name:
                    routes.add("/login")
                elif "Dashboard" in name or "dashboard" in name:
                    routes.add("/dashboard")
                elif "Profile" in name or "profile" in name:
                    routes.add("/profile")
                elif "Home" in name or "home" in name:
                    routes.add("/")
                else:
                    # Usar nombre del archivo como ruta
                    route = "/" + name.lower().replace("_", "-")
                    routes.add(route)
            
            # Detectar cambios en App.js o rutas
            if "App.js" in filename or "routes.js" in filename or "router.js" in filename:
                # Por defecto ir a home
                routes.add("/")
        
        return list(routes)
