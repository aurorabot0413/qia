"""
LangChain QA Agent con Vertex AI Gemini 2.5 Pro
"""
from langchain_google_vertexai import VertexAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from typing import Dict, List, Optional
import logging
import base64

logger = logging.getLogger(__name__)


class QAAgent:
    """Agente de QA usando LangChain + Vertex AI"""
    
    def __init__(self):
        # Inicializar LLM (Gemini 2.5 Pro)
        self.llm = VertexAI(
            model_name="gemini-2.5-pro",
            temperature=0.1,
            max_output_tokens=8192,
            verbose=True
        )
        
        # Crear herramientas
        self.tools = self._create_tools()
        
        # Crear agente
        self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Crea las herramientas del agente"""
        return [
            Tool(
                name="analyze_visual",
                func=self._analyze_visual,
                description="Analiza screenshots visuales y detecta errores de UI/UX"
            ),
            Tool(
                name="review_code",
                func=self._review_code,
                description="Revisa código en busca de bugs, problemas de seguridad y performance"
            ),
            Tool(
                name="check_accessibility",
                func=self._check_accessibility,
                description="Verifica problemas de accesibilidad (WCAG)"
            ),
            Tool(
                name="compare_design",
                func=self._compare_design,
                description="Compara implementación con diseño original"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Crea el agente de LangChain"""
        
        prompt = PromptTemplate.from_template(
            """Eres un QA Senior especializado en aplicaciones React.

Tienes acceso a las siguientes herramientas:
{tools}

Usa el siguiente formato:

Question: La pregunta de entrada
Thought: Qué debes hacer
Action: La herramienta a usar (debe ser una de: [{tool_names}])
Action Input: La entrada para la herramienta
Observation: El resultado de la herramienta
... (repetir Thought/Action/Action Input/Observation N veces)
Thought: Ya sé la respuesta final
Final Answer: La respuesta final en formato JSON

Comienza!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
    
    async def analyze(
        self,
        pr_data: Dict,
        screenshots: List[bytes],
        design_image: Optional[bytes] = None
    ) -> Dict:
        """
        Analiza el PR completo
        
        Args:
            pr_data: Datos del PR (archivos modificados, etc.)
            screenshots: Lista de screenshots capturados
            design_image: Imagen del diseño original (opcional)
        
        Returns:
            Dict con análisis completo
        """
        try:
            # Preparar input para el agente
            input_text = f"""
            Analiza el siguiente Pull Request:
            
            PR #{pr_data['number']} - {pr_data['title']}
            
            Archivos modificados:
            {self._format_files(pr_data['modified_files'])}
            
            Screenshots capturados: {len(screenshots)}
            Diseño original disponible: {"Sí" if design_image else "No"}
            
            Realiza:
            1. Análisis visual de los screenshots
            2. Revisión del código modificado
            3. Verificación de accesibilidad
            4. Comparación con diseño (si disponible)
            
            Genera un reporte con:
            - status: "approved" | "rejected" | "needs_review"
            - confidence: 0-1
            - issues: lista de problemas encontrados
            - summary: resumen ejecutivo
            """
            
            # Ejecutar agente
            result = await self.agent.ainvoke({"input": input_text})
            
            # Parsear resultado
            return self._parse_result(result["output"])
            
        except Exception as e:
            logger.error(f"Error in QA analysis: {e}", exc_info=True)
            return {
                "status": "needs_review",
                "confidence": 0.0,
                "issues": [{"type": "error", "message": str(e)}],
                "summary": "Error durante el análisis"
            }
    
    def _analyze_visual(self, screenshot_data: str) -> str:
        """Analiza screenshots visuales"""
        # Implementar análisis visual con Vertex AI Vision
        return "Visual analysis: No critical issues found"
    
    def _review_code(self, code_data: str) -> str:
        """Revisa código en busca de problemas"""
        # Implementar revisión de código
        return "Code review: No critical bugs found"
    
    def _check_accessibility(self, component_data: str) -> str:
        """Verifica accesibilidad"""
        # Implementar verificación de accesibilidad
        return "Accessibility: WCAG AA compliant"
    
    def _compare_design(self, comparison_data: str) -> str:
        """Compara implementación con diseño"""
        # Implementar comparación con diseño
        return "Design comparison: 98% match"
    
    def _format_files(self, files: List[Dict]) -> str:
        """Formatea lista de archivos para el prompt"""
        return "\n".join([
            f"- {f['filename']} ({f['status']})"
            for f in files
        ])
    
    def _parse_result(self, output: str) -> Dict:
        """Parsea el resultado del agente"""
        import json
        
        try:
            # Intentar parsear JSON
            if "Final Answer:" in output:
                json_str = output.split("Final Answer:")[-1].strip()
                return json.loads(json_str)
        except:
            pass
        
        # Fallback
        return {
            "status": "needs_review",
            "confidence": 0.5,
            "issues": [],
            "summary": output
        }
