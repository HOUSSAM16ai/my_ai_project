"""
Local Knowledge Base Retrieval (Fallback Mechanism).
Infrastructure Layer.
"""
from pathlib import Path
from typing import Optional

import yaml

from app.core.logging import get_logger
from app.services.chat.tools.retrieval import parsing

logger = get_logger("tool-retrieval-local")


def search_local_knowledge_base(
    query: str,
    year: Optional[str],
    subject: Optional[str],
    branch: Optional[str],
    exam_ref: Optional[str],
) -> str:
    """
    بحث احتياطي في الملفات المحلية في حال تعطل خدمة الذاكرة أو عدم وجود نتائج.
    """
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        return "قاعدة المعرفة المحلية غير موجودة."

    matches = []

    for md_file in kb_path.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")

            # Extract frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter_raw = parts[1]
                    body = parts[2]

                    try:
                        metadata = yaml.safe_load(frontmatter_raw)
                        meta_dict = metadata.get("metadata", {})

                        # Flexible Matching Logic for Fallback

                        # 1. Check Year
                        if year and str(meta_dict.get("year", "")) != str(year):
                            continue

                        # 2. Check Subject
                        if subject:
                            file_subject = str(meta_dict.get("subject", "")).lower()
                            if subject.lower() not in file_subject and file_subject not in subject.lower():
                                continue

                        # 3. Check Branch
                        if branch:
                            file_branch = meta_dict.get("branch", "")
                            branch_query = branch.lower()
                            if isinstance(file_branch, list):
                                if not any(b.lower() in branch_query or branch_query in b.lower() for b in file_branch):
                                    continue
                            else:
                                if str(file_branch).lower() not in branch_query and branch_query not in str(file_branch).lower():
                                    continue

                        # 4. Check Exam Ref
                        if exam_ref:
                            file_ref = str(meta_dict.get("exam_ref", "")).lower()
                            if exam_ref.lower() not in file_ref and file_ref not in exam_ref.lower():
                                continue

                        # 5. Extract Specific Exercise if requested
                        extracted_exercise = parsing.extract_specific_exercise(body, query)

                        is_specific = parsing.is_specific_request(query)

                        if extracted_exercise:
                            matches.append(extracted_exercise)
                        elif not is_specific:
                            # Only append full body if request was NOT specific
                            matches.append(body.strip())

                    except yaml.YAMLError:
                        logger.error(f"Failed to parse YAML in {md_file}")
                        continue
        except Exception as e:
            logger.error(f"Error reading file {md_file}: {e}")
            continue

    if not matches:
        return "لم يتم العثور على محتوى مطابق في الملفات المحلية (وضع عدم الاتصال)."

    # Deduplicate matches
    unique_matches = parsing.deduplicate_contents(matches)

    return "\n\n".join(unique_matches[:3]).strip()
