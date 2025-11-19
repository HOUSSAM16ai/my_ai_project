# app/services/prompt_engineering_service.py
from sqlalchemy.orm import Session
from app.models import GeneratedPrompt, PromptTemplate, User

class PromptEngineeringService:
    def generate_prompt(
        self,
        db: Session,
        user_description: str,
        user: User,
        template_id: int | None = None,
    ) -> dict[str, any]:
        template = None
        if template_id:
            template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()

        generated_prompt_text = f"User wants: {user_description}"
        if template:
            generated_prompt_text = template.template.format(user_description=user_description)

        generated_record = GeneratedPrompt(
            prompt=generated_prompt_text,
            template_id=template.id if template else None,
        )
        db.add(generated_record)
        db.commit()
        db.refresh(generated_record)

        return {
            "status": "success",
            "prompt_id": generated_record.id,
            "generated_prompt": generated_prompt_text,
        }

    def create_template(
        self,
        db: Session,
        name: str,
        template_content: str,
        user: User,
    ) -> dict[str, any]:
        template = PromptTemplate(
            name=name,
            template=template_content,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return {"status": "success", "template_id": template.id}

prompt_engineering_service = PromptEngineeringService()
