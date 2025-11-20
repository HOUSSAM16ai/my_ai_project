# app/services/prompt_engineering_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models import PromptTemplate, GeneratedPrompt, User
import logging

logger = logging.getLogger(__name__)

class PromptEngineeringService:
    async def generate_prompt(
        self,
        db: AsyncSession,
        user: User,
        template_name: str,
        variables: dict,
        user_description: str | None = None
    ) -> str:
        result = await db.execute(select(PromptTemplate).where(PromptTemplate.name == template_name))
        template = result.scalars().first()

        if not template:
            template = PromptTemplate(name=template_name, template="Default template: {prompt}")
            db.add(template)
            await db.commit()
            await db.refresh(template)

        prompt_text = template.template.format(**variables)

        generated_record = GeneratedPrompt(
            prompt=prompt_text,
            template_id=template.id
        )
        db.add(generated_record)
        await db.commit()
        await db.refresh(generated_record)

        return prompt_text

prompt_engineering_service = PromptEngineeringService()
