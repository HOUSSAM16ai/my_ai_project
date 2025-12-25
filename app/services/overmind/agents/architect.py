# app/services/overmind/agents/architect.py
"""
الوكيل المعماري (Architect Agent) - المصمم التقني.
---------------------------------------------------------
يقوم هذا الوكيل بتحويل الخطة الاستراتيجية (النظرية) إلى تصميم تقني قابل للتنفيذ
(Technical Specification). يحدد الأدوات الدقيقة والمعاملات المطلوبة لكل خطوة.

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
- استخدام واجهات صارمة.
"""

import json
from typing import Any

from app.core.ai_gateway import AIClient
from app.core.di import get_logger
from app.core.protocols import AgentArchitect, CollaborationContext

logger = get_logger(__name__)


class ArchitectAgent(AgentArchitect):
    """
    المهندس المعماري للنظام.

    المسؤوليات:
    1. ترجمة الخطوات البشرية (Human Steps) إلى مهام تقنية (Technical Tasks).
    2. اختيار الأدوات المناسبة من السجل (Tool Registry) لكل مهمة.
    3. صياغة المعاملات (Arguments) بصيغة JSON دقيقة.
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai = ai_client

    async def design_solution(self, plan: dict[str, Any], context: CollaborationContext) -> dict[str, Any]:
        """
        تحويل الخطة الاستراتيجية إلى تصميم تقني.

        Args:
            plan (dict): الخطة الناتجة عن الاستراتيجي (Strategist).
            context (CollaborationContext): السياق المشترك.

        Returns:
            dict: تصميم يحتوي على قائمة المهام الجاهزة للتنفيذ.
        """
        logger.info("Architect is designing the technical solution...")

        system_prompt = """
        أنت "المعماري" (The Architect)، خبير تقني ضمن منظومة Overmind.

        مهمتك:
        تحويل خطوات الخطة الاستراتيجية إلى مهام تقنية دقيقة قابلة للتنفيذ بواسطة أدوات النظام.

        الأدوات المتاحة (Common Tools):
        - read_file(filepath)
        - write_file(filepath, content)
        - list_files(path)
        - run_shell(command) (Use carefully)
        - git_status()
        - git_commit(message)

        القواعد:
        1. كل خطوة في الخطة يجب أن تتحول إلى مهمة واحدة أو أكثر.
        2. يجب تحديد اسم الأداة (tool_name) بدقة.
        3. معاملات الأداة (tool_args) يجب أن تكون JSON object.
        4. المخرجات يجب أن تكون JSON صالح فقط.

        صيغة JSON المطلوبة:
        {
            "design_name": "اسم التصميم",
            "tasks": [
                {
                    "name": "اسم المهمة",
                    "tool_name": "write_file",
                    "tool_args": {"filepath": "src/main.py", "content": "print('hello')"},
                    "description": "وصف تقني"
                }
            ]
        }
        """

        plan_str = json.dumps(plan, default=str)
        user_content = f"Plan: {plan_str}\nConvert this into executable tasks."

        try:
            logger.info("Architect: Calling AI for design generation...")
            response_text = await self.ai.send_message(
                system_prompt=system_prompt,
                user_message=user_content,
                temperature=0.1  # دقة قصوى
            )
            logger.info(f"Architect: Received AI response ({len(response_text)} chars)")

            cleaned_response = self._clean_json_block(response_text)
            design_data = json.loads(cleaned_response)

            if "tasks" not in design_data:
                raise ValueError("Design missing 'tasks' field")

            logger.info(f"Architect: Design created with {len(design_data.get('tasks', []))} tasks")
            # تخزين التصميم في الذاكرة المشتركة
            context.update("last_design", design_data)
            return design_data

        except json.JSONDecodeError as e:
            logger.error(f"Architect JSON parsing error: {e}")
            logger.error(f"Raw response: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
            return {
                "design_name": "Failed Design - JSON Error",
                "error": f"JSON parsing failed: {e}",
                "tasks": []
            }
        except Exception as e:
            logger.exception(f"Architect failed to design: {e}")
            # في حال الفشل، نعيد تصميم فارغ أو خطأ
            return {
                "design_name": "Failed Design",
                "error": f"{type(e).__name__}: {e!s}",
                "tasks": []
            }

    def _clean_json_block(self, text: str) -> str:
        """استخراج JSON من نص قد يحتوي على Markdown code blocks."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
